# pylint: disable=no-name-in-module
from __future__ import annotations

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import RephraserOptions as ProtoRephraserOptions

from yandex_cloud_ml_sdk._types.model import BaseModel
from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig
from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType
from yandex_cloud_ml_sdk._types.result import BaseResult


class RephraserConfig(BaseModelConfig):
    pass


class _RephraserPseudoResult(BaseResult):
    pass


class Rephraser(BaseModel[RephraserConfig, _RephraserPseudoResult], ProtoBased[ProtoRephraserOptions]):
    """Class for incapsulating rephraser settings.

    Used to rewrite the last user message for search,
    incorporating context from the previous conversation.
    """

    _config_type = RephraserConfig
    _result_type = _RephraserPseudoResult

    def _to_proto(self) -> ProtoRephraserOptions:
        return ProtoRephraserOptions(
            rephraser_uri=self.uri,
        )

    @classmethod
    def _from_proto(cls, *, proto: ProtoRephraserOptions, sdk: SDKType) -> Self:
        return cls(
            sdk=sdk,
            uri=proto.rephraser_uri
        )
