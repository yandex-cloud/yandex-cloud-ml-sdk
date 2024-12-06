from __future__ import annotations

from typing import TYPE_CHECKING, Any

from grpc import StatusCode
from grpc.aio import AioRpcError as BaseAioRpcError
from grpc.aio import Metadata

from ._auth import BaseAuth

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from ._client import StubType
    from ._types.operation import OperationErrorInfo
    from ._datasets.validation import DatasetValidationResult


class YCloudMLError(Exception):
    pass


class RunError(YCloudMLError):
    def __init__(self, code: int, message: str, details: list[Any] | None, operation_id: str):
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
    def from_proro_status(cls, status: OperationErrorInfo, operation_id: str):
        return cls(
            code=status.code,
            message=status.message,
            details=list(status.details) if status.details else None,
            operation_id=operation_id,
        )


class AsyncOperationError(YCloudMLError):
    pass


class WrongAsyncOperationStatusError(AsyncOperationError):
    pass


class DatasetValidationError(AsyncOperationError):
    def __init__(self, validation_result: DatasetValidationResult):
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


class AioRpcError(BaseAioRpcError):
    _initial_metadata: Metadata | None
    _trailing_metadata: Metadata | None

    def __init__(
        self,
        *args,
        endpoint: str,
        auth: BaseAuth | None,
        stub_class: type[StubType],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._endpoint = endpoint
        self._auth = auth
        self._stub_class = stub_class

        self._client_request_id: str

        initial = self._initial_metadata
        trailing = self._trailing_metadata

        if (
            initial is not None and not isinstance(initial, Metadata) or
            trailing is not None and not isinstance(trailing, Metadata)
        ):
            self._client_request_id = "grpc metadata was replaced with non-Metadata object"
        else:
            self._client_request_id = (
                initial and initial.get('x-client-request-id') or
                trailing and trailing.get('x-client-request-id') or
                ""
            )

    @classmethod
    def from_base_rpc_error(
        cls,
        original: BaseAioRpcError,
        endpoint: str,
        auth: BaseAuth | None,
        stub_class: type[StubType],
    ) -> AioRpcError:
        return cls(
            code=original.code(),
            initial_metadata=original.initial_metadata(),
            trailing_metadata=original.trailing_metadata(),
            details=original.details(),
            debug_error_string=original.debug_error_string(),
            endpoint=endpoint,
            auth=auth,
            stub_class=stub_class,
        ).with_traceback(original.__traceback__)

    def __str__(self):
        parts = [
            f"code = {self._code}",
            f'details = "{self._details}"',
            f'debug_error_string = "{self._debug_error_string}"',
            f'endpoint = "{self._endpoint}"',
            f'stub_class = {self._stub_class.__name__}'
        ]

        if self._client_request_id:
            parts.append(f'x-client-request-id = "{self._client_request_id}"')

        if self._code == StatusCode.UNAUTHENTICATED:
            auth = self._auth.__class__.__name__ if self._auth else None
            parts.append(
                f"auth_provider = {auth}"
            )

        body = '\n'.join(f'\t{part}' for part in parts)

        return f"<{self.__class__.__name__} of RPC that terminated with:\n{body}\n>"


class TuningError(RunError):
    def __str__(self):
        return f'Tuning task {self.operation_id} failed'
