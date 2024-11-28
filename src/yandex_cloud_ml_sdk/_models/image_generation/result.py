from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_service_pb2 import ImageGenerationResponse

from yandex_cloud_ml_sdk._types.result import BaseResult, ProtoMessage

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclass(frozen=True, repr=False)
class ImageGenerationModelResult(BaseResult):
    image_bytes: bytes
    model_version: str

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> Self:  # pylint: disable=unused-argument
        proto = cast(ImageGenerationResponse, proto)
        return cls(
            image_bytes=proto.image,
            model_version=proto.model_version,
        )

    def _repr_jpeg_(self) -> bytes | None:
        # NB: currently model could return only jpeg,
        # but for future I will put this check here to
        # remember we will need to make a _repr_png_ and such
        if (
            self.image_bytes[:2] == bytes.fromhex("FFD8") and
            self.image_bytes[-2:] == bytes.fromhex("FFD9")
        ):
            return self.image_bytes
        return None

    def __repr__(self) -> str:
        size = len(self.image_bytes)
        return f'{self.__class__.__name__}(model_version={self.model_version!r}, image_bytes=<{size} bytes>)'
