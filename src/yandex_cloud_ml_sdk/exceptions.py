from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
from typing import Any as _Any

if _TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from yandex_cloud_ml_sdk._datasets.validation import DatasetValidationResult as _DatasetValidationResult
    from yandex_cloud_ml_sdk._types.operation import OperationErrorInfo as _OperationErrorInfo


class YCloudMLError(Exception):
    pass


class RunError(YCloudMLError):
    def __init__(self, code: int, message: str, details: list[_Any] | None, operation_id: str):
        self.code = code
        self.message = message
        self.details = details or []
        self.operation_id = operation_id

    def __str__(self):
        message = self.message or "<Empty message>"
        message = f'Operation {self.operation_id} failed with message: {message} (code {self.code})'
        message += '\n' + '\n'.join(repr(d) for d in self.details)
        return message

    @classmethod
    def from_proro_status(cls, status: _OperationErrorInfo, operation_id: str):
        return cls(
            code=status.code,
            message=status.message,
            details=list(status.details) if status.details else None,
            operation_id=operation_id,
        )


class TuningError(RunError):
    def __str__(self):
        return f'Tuning task {self.operation_id} failed'


class AsyncOperationError(YCloudMLError):
    pass


class WrongAsyncOperationStatusError(AsyncOperationError):
    pass


class DatasetValidationError(AsyncOperationError):
    def __init__(self, validation_result: _DatasetValidationResult):
        self._result = validation_result

        errors_str = '\n'.join(str(error) for error in self.errors)
        message = f"Dataset validation for dataset_id={self.dataset_id} failed with next errors:\n{errors_str}"
        super().__init__(message)

    @property
    def errors(self):
        return self._result.errors

    @property
    def dataset_id(self):
        return self._result.dataset_id
