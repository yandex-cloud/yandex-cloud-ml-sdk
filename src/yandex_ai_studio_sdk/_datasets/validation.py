# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from yandex.cloud.ai.dataset.v1.dataset_pb2 import ValidationError as ProtoValidationError
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import ValidateDatasetResponse
from yandex_ai_studio_sdk._types.proto import ProtoBased
from yandex_ai_studio_sdk._types.result import BaseProtoResult
from yandex_ai_studio_sdk.exceptions import DatasetValidationError

if TYPE_CHECKING:
    from yandex_ai_studio_sdk._sdk import BaseSDK


@dataclass(frozen=True)
class ValidationErrorInfo(ProtoBased[ProtoValidationError]):
    """A class which represents information about a validation error in a dataset."""
    #: the error message indicating what went wrong
    error: str
    #: a detailed description of the error
    description: str
    #: the row numbers associated with the error
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
    """A class which represents the result of validating a dataset."""
    _sdk: BaseSDK = field(repr=False)
    #: the ID of the dataset being validated
    dataset_id: str
    #: the parameter which indicates whether the dataset is valid
    is_valid: bool
    #: a tuple of validation errors encountered during validation
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
        """Raises a DatasetValidationError if the dataset had any problems during creation and validation."""
        if not self.is_valid:
            raise DatasetValidationError(self)
