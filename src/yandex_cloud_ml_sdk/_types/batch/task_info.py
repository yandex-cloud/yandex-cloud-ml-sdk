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
    line_number: int
    message: str


@dataclass(frozen=True)
class BatchErrorInfo(ProtoMirrored[ProtoBatchInferenceTask.ErrorsInfo.BatchError]):
    batch_number: int
    first_line: int
    last_line: int
    message: str


@dataclass(frozen=True)
class BatchTaskErrorsInfo(ProtoMirrored[ProtoBatchInferenceTask.ErrorsInfo]):
    line_errors: tuple[LineErrorInfo, ...]
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
    task_id: str
    operation_id: str
    folder_id: str
    model_uri: str

    source_dataset_id: str
    result_dataset_id: str | None

    status: BatchTaskStatus
    labels: dict[str, str]

    created_by: str
    created_at: datetime
    started_at: datetime
    finished_at: datetime

    errors: BatchTaskErrorsInfo

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoBatchInferenceTask, sdk: SDKType) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)

        kwargs['errors'] = BatchTaskErrorsInfo._from_proto(proto=proto.errors, sdk=sdk)
        kwargs['status'] = BatchTaskStatus._from_proto(proto=proto.status)
        return kwargs
