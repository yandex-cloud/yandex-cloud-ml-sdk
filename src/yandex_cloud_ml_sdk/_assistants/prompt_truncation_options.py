# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Literal, Union

from google.protobuf.wrappers_pb2 import Int64Value
from typing_extensions import TypeAlias
from yandex.cloud.ai.assistants.v1.common_pb2 import PromptTruncationOptions as ProtoPromptTruncationOptions

from yandex_cloud_ml_sdk._types.misc import Undefined, get_defined_value, is_defined
from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType

PromptTruncationStrategyType: TypeAlias = Union[Literal['auto'], 'BasePromptTruncationStrategy']
ProtoPromptTruncationStrategy: TypeAlias = Union[
    ProtoPromptTruncationOptions.AutoStrategy,
    ProtoPromptTruncationOptions.LastMessagesStrategy
]


@dataclass(frozen=True)
class PromptTruncationOptions(ProtoBased[ProtoPromptTruncationOptions]):
    #: The maximum number of tokens allowed in the prompt.
    #: If the prompt exceeds this limit, the thread messages will be truncated.
    #: Default max_prompt_tokens: 7000
    max_prompt_tokens: int | None = None
    strategy: BasePromptTruncationStrategy | None = None

    @property
    def _auto_strategy(self) -> AutoPromptTruncationStrategy | None:
        if isinstance(self.strategy, AutoPromptTruncationStrategy):
            return self.strategy
        return None

    @property
    def _last_messages_strategy(self) -> LastMessagesPromptTruncationStrategy | None:
        if isinstance(self.strategy, LastMessagesPromptTruncationStrategy):
            return self.strategy
        return None

    @classmethod
    def _from_proto(cls, proto: ProtoPromptTruncationOptions, sdk: SDKType) -> PromptTruncationOptions:
        kwargs = {}
        if proto.HasField('max_prompt_tokens'):
            kwargs['max_prompt_tokens'] = proto.max_prompt_tokens.value
        return cls(
            strategy=BasePromptTruncationStrategy._from_upper_proto(proto=proto, sdk=sdk),
            **kwargs
        )

    def _to_proto(self) -> ProtoPromptTruncationOptions:
        max_prompt_tokens = None if self.max_prompt_tokens is None else Int64Value(value=self.max_prompt_tokens)
        return ProtoPromptTruncationOptions(
            max_prompt_tokens=max_prompt_tokens,
            last_messages_strategy=self._last_messages_strategy._to_proto() if self._last_messages_strategy else None,
            auto_strategy=self._auto_strategy._to_proto() if self._auto_strategy else None,
        )

    @classmethod
    def _coerce(
        cls,
        *,
        max_prompt_tokens: int | Undefined,
        strategy: PromptTruncationStrategyType | Undefined,
    ) -> PromptTruncationOptions:
        return cls(
            max_prompt_tokens=get_defined_value(max_prompt_tokens, None),
            strategy=(
                # this type is to complicated for mypy and it thinks it is "object"
                BasePromptTruncationStrategy._coerce(strategy)  # type: ignore[arg-type]
                if is_defined(strategy)
                else None
            )
        )

    def _get_update_paths(self) -> dict[str, bool]:
        update_paths: dict[str, bool] = {}
        for path, value in (
            ('max_prompt_tokens', self.max_prompt_tokens),
            ('auto_strategy', self._auto_strategy),
            ('last_messages_strategy', self._last_messages_strategy),
        ):
            if value is not None:
                full_path = f'prompt_truncation_options.{path}'
                update_paths[full_path] = True
        return update_paths


class BasePromptTruncationStrategy(ProtoBased[ProtoPromptTruncationOptions]):
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, proto: ProtoPromptTruncationOptions, sdk: SDKType) -> BasePromptTruncationStrategy:
        pass

    @abc.abstractmethod
    def _to_proto(self) -> ProtoPromptTruncationStrategy:
        pass

    @classmethod
    def _coerce(cls, strategy: PromptTruncationStrategyType) -> BasePromptTruncationStrategy:
        if isinstance(strategy, BasePromptTruncationStrategy):
            return strategy

        if strategy == 'auto':
            return AutoPromptTruncationStrategy()
        raise TypeError(
            'prompt truncation strategy could be "auto" string literal '
            'or a BasePromptTruncationStrategy class instance'
        )

    @classmethod
    def _from_upper_proto(cls, proto: ProtoPromptTruncationOptions, sdk: SDKType) -> BasePromptTruncationStrategy:
        klass: type[LastMessagesPromptTruncationStrategy | AutoPromptTruncationStrategy]
        if proto.HasField('auto_strategy'):
            klass = AutoPromptTruncationStrategy
        elif proto.HasField('last_messages_strategy'):
            klass = LastMessagesPromptTruncationStrategy
        else:
            raise NotImplementedError(
                'prompt truncation strategies other then Auto and LastMessages are not supported in this SDK version'
            )
        return klass._from_proto(proto=proto, sdk=sdk)


@dataclass(frozen=True)
class AutoPromptTruncationStrategy(BasePromptTruncationStrategy):
    """The system will handle truncation in a way that aims to preserve the most relevant context."""

    @classmethod
    def _from_proto(cls, proto: ProtoPromptTruncationOptions, sdk: SDKType) -> AutoPromptTruncationStrategy:
        return cls()

    def _to_proto(self) -> ProtoPromptTruncationOptions.AutoStrategy:
        return ProtoPromptTruncationOptions.AutoStrategy()


@dataclass(frozen=True)
class LastMessagesPromptTruncationStrategy(BasePromptTruncationStrategy):
    """Specifies the truncation strategy to use when the prompt exceeds the token limit."""

    #: The number of most recent messages to retain in the prompt.
    #: If these messages exceed `max_prompt_tokens`, older messages will be further truncated to fit the limit.
    num_messages: int

    @classmethod
    def _from_proto(cls, proto: ProtoPromptTruncationOptions, sdk: SDKType) -> LastMessagesPromptTruncationStrategy:
        return LastMessagesPromptTruncationStrategy(
            num_messages=proto.last_messages_strategy.num_messages,
        )

    def _to_proto(self) -> ProtoPromptTruncationOptions.LastMessagesStrategy:
        return ProtoPromptTruncationOptions.LastMessagesStrategy(
            num_messages=self.num_messages
        )
