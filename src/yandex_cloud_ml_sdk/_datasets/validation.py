# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from yandex.cloud.ai.dataset.v1.dataset_pb2 import ValidationError as ProtoValidationError
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import ValidateDatasetResponse

from yandex_cloud_ml_sdk._types.result import BaseResult, ProtoMessage

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclass(frozen=True)
class ValidationErrorInfo:
    error: str
    description: str
    rows: tuple[int, ...]

    # pylint: disable=unused-argument
    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> ValidationErrorInfo:
        proto = cast(ProtoValidationError, proto)
        return cls(
            error=proto.error,
            description=proto.error_description,
            rows=tuple(proto.row_numbers)
        )


class ValidationError(RuntimeError):
    def __init__(self, dataset_id: str, errors: tuple[ValidationErrorInfo, ...]):
        self._dataset_id = dataset_id
        self._errors = errors

    def __str__(self) -> str:
        errors_str = '\n'.join(str(error) for error in self._errors)
        return f"Dataset validation for dataset_id={self._dataset_id} failed with next errors:\n{errors_str}"


@dataclass(frozen=True)
class DatasetValidationResult(BaseResult):
    dataset_id: str
    is_valid: bool
    errors: tuple[ValidationErrorInfo, ...]

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> DatasetValidationResult:
        proto = cast(ValidateDatasetResponse, proto)

        return cls(
            dataset_id=proto.dataset_id,
            is_valid=proto.is_valid,
            errors=tuple(
                ValidationErrorInfo._from_proto(proto=error, sdk=sdk)
                for error in proto.errors
            )
        )

    def raise_for_status(self) -> None:
        if not self.is_valid:
            raise ValidationError(self.dataset_id, self.errors)
