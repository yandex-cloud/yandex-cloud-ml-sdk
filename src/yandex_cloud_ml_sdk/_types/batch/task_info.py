# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from yandex.cloud.ai.batch_inference.v1.batch_inference_task_pb2 import BatchInferenceTask as ProtoBatchInferenceTask

from yandex_cloud_ml_sdk._types.proto import ProtoMirrored, SDKType

from .status import BatchTaskStatus


@dataclass(frozen=True)
class LineErrorInfo(ProtoMirrored[ProtoBatchInferenceTask.ErrorsInfo.LineError]):
    """
    Information about a line-specific error in batch inference.

    This class represents details about an error that occurred
    while processing a specific line in a batch inference task.
    """
    #: The line number where the error occurred
    line_number: int
    #: The error message describing what went wrong
    message: str


@dataclass(frozen=True)
class BatchErrorInfo(ProtoMirrored[ProtoBatchInferenceTask.ErrorsInfo.BatchError]):
    """
    Information about a batch-specific error in batch inference.

    This class represents details about an error that occurred
    while processing a specific batch in a batch inference task.
    """
    #: The batch number where the error occurred
    batch_number: int
    #: The first line number in the batch that had an error
    first_line: int
    #: The last line number in the batch that had an error
    last_line: int
    #: The error message describing what went wrong
    message: str


@dataclass(frozen=True)
class BatchTaskErrorsInfo(ProtoMirrored[ProtoBatchInferenceTask.ErrorsInfo]):
    """
    Comprehensive error information for a batch inference task.

    This class aggregates all error information that occurred during
    a batch inference task, including both line-specific and batch-specific errors.
    """
    #: Tuple of line-specific error information
    line_errors: tuple[LineErrorInfo, ...]
    #: Tuple of batch-specific error information
    batch_errors: tuple[BatchErrorInfo, ...]

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoBatchInferenceTask.ErrorsInfo, sdk: SDKType) -> dict[str, Any]:
        return {
            'line_errors': tuple(
                LineErrorInfo._from_proto(proto=line_error, sdk=sdk)
                for line_error in proto.line_errors
            ),
            'batch_errors': tuple(
                BatchErrorInfo._from_proto(proto=batch_error, sdk=sdk)
                for batch_error in proto.batch_errors
            )
        }


@dataclass(frozen=True)
class BatchTaskInfo(ProtoMirrored[ProtoBatchInferenceTask]):
    """
    Complete information about a batch inference task.

    This class contains all relevant information about a batch inference task,
    including its metadata, execution details, timing information, and any errors
    that occurred during processing.
    """
    #: Unique identifier for the batch task
    task_id: str
    #: Identifier for the operation associated with this task
    operation_id: str
    #: Identifier for the folder containing this task
    folder_id: str
    #: URI of the model used for inference
    model_uri: str
    #: Identifier for the input dataset
    source_dataset_id: str
    #: Identifier for the output dataset, if available
    result_dataset_id: str | None
    #: Current status of the batch task
    status: BatchTaskStatus
    #: Dictionary of user-defined labels for the task
    labels: dict[str, str]
    #: Identifier of the user who created the task
    created_by: str
    #: Timestamp when the task was created
    created_at: datetime
    #: Timestamp when the task execution started
    started_at: datetime
    #: Timestamp when the task execution finished
    finished_at: datetime
    #: Comprehensive error information for the task
    errors: BatchTaskErrorsInfo

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoBatchInferenceTask, sdk: SDKType) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)

        kwargs['errors'] = BatchTaskErrorsInfo._from_proto(proto=proto.errors, sdk=sdk)
        kwargs['status'] = BatchTaskStatus._from_proto(proto=proto.status)
        return kwargs
