from __future__ import annotations

from typing import Literal, Union, cast

from typing_extensions import TypeAlias
# pylint: disable=no-name-in-module
from yandex.cloud.ai.assistants.v1.common_pb2 import CallStrategy as ProtoCallStrategy

from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType
from yandex_cloud_ml_sdk._types.tools.function import FunctionDictType, validate_function_dict

#: Type alias for string-based call strategy. Currently only supports 'always' value.
CallStrategyStringType: TypeAlias = Literal['always']

#: Type alias for all supported call strategy types. Can be either: a string literal ('always') or a function dictionary with instruction
CallStrategyType: TypeAlias = Union[CallStrategyStringType, FunctionDictType]

#: Type alias for call strategy input types. Can be either: a CallStrategyType (string or function dict) or existing CallStrategy instance
CallStrategyInputType: TypeAlias = Union[CallStrategyType, 'CallStrategy']


class CallStrategy(ProtoBased[ProtoCallStrategy]):
    """
    Represents call strategy for search index tools.

    The call strategy determines when a tool should be called:
    - 'always': call the tool on every request
    - function dict: call based on function instruction
    """
    _call_strategy: CallStrategyType

    def __init__(self, call_strategy: CallStrategyType):
        self._call_strategy = call_strategy
        self._validate()

    @property
    def value(self) -> CallStrategyType:
        """
        Get the current call strategy value.
        """
        return self._call_strategy

    def _validate(self):
        call_strategy = self.value
        if isinstance(call_strategy, str):
            if call_strategy == 'always':
                return
        elif isinstance(call_strategy, dict):
            call_strategy = validate_function_dict(call_strategy)
            if 'instruction' in call_strategy['function']:
                return

        raise ValueError(
            f'wrong {call_strategy=}, '
            'expected `call_strategy="always"` or'
            '`call_strategy={"type": "function", "function": {"name": str, "instruction": str}}`'
        )

    # pylint: disable=unused-argument
    @classmethod
    def _from_proto(cls, *, proto: ProtoCallStrategy, sdk: SDKType) -> CallStrategy:
        value: CallStrategyType
        if proto.HasField('auto_call'):
            value = {
                'type': 'function',
                'function': {'name': proto.auto_call.name, 'instruction': proto.auto_call.instruction}
            }
        elif proto.HasField('always_call'):
            value = 'always'
        else:
            raise RuntimeError(
                "proto message CallStrategy have unknown fields, try to upgrade yandex-cloud-ml-sdk")
        return cls(value)

    def _to_proto(self) -> ProtoCallStrategy:
        if self._call_strategy == 'always':
            return ProtoCallStrategy(
                always_call=ProtoCallStrategy.AlwaysCall()
            )
        call_strategy = cast(FunctionDictType, self._call_strategy)
        function = call_strategy['function']
        assert 'instruction' in function
        return ProtoCallStrategy(
            auto_call=ProtoCallStrategy.AutoCall(
                name=function['name'],
                instruction=function['instruction']
            )
        )

    @classmethod
    def _coerce(cls, call_strategy: CallStrategyInputType):
        if isinstance(call_strategy, CallStrategy):
            return call_strategy

        return cls(call_strategy)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"
