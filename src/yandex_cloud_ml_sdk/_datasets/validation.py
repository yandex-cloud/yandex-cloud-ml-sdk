# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from yandex.cloud.ai.dataset.v1.dataset_pb2 import ValidationError as ProtoValidationError
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import ValidateDatasetResponse

from yandex_cloud_ml_sdk._types.proto import ProtoBased
from yandex_cloud_ml_sdk._types.result import BaseProtoResult
from yandex_cloud_ml_sdk.exceptions import DatasetValidationError

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclass(frozen=True)
class ValidationErrorInfo(ProtoBased[ProtoValidationError]):
    error: str
    description: str
    rows: tuple[int, ...]

    # pylint: disable=unused-argument
    @classmethod
    def _from_proto(cls, *, proto: ProtoValidationError, sdk: BaseSDK) -> ValidationErrorInfo:
        return cls(
            error=proto.error,
            description=proto.error_description,
            rows=tuple(proto.row_numbers)
        )


@dataclass(frozen=True)
class DatasetValidationResult(BaseProtoResult[ValidateDatasetResponse]):
    _sdk: BaseSDK = field(repr=False)
    dataset_id: str
    is_valid: bool
    errors: tuple[ValidationErrorInfo, ...]

    @classmethod
    def _from_proto(cls, *, proto: ValidateDatasetResponse, sdk: BaseSDK) -> DatasetValidationResult:
        return cls(
            dataset_id=proto.dataset_id,
            is_valid=proto.is_valid,
            errors=tuple(
                ValidationErrorInfo._from_proto(proto=error, sdk=sdk)
                for error in proto.errors
            ),
            _sdk=sdk,
        )

    def raise_for_status(self) -> None:
        if not self.is_valid:
            raise DatasetValidationError(self)
