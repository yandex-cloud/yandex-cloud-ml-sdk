# pylint: disable=no-name-in-module
from __future__ import annotations

from enum import IntEnum

from yandex.cloud.ai.batch_inference.v1.batch_inference_task_pb2 import BatchInferenceTask as ProtoBatchInferenceTask

from yandex_cloud_ml_sdk._types.operation import BaseOperationStatus
from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase

_base = ProtoBatchInferenceTask.Status


class BatchTaskStatus(BaseOperationStatus, ProtoEnumBase, IntEnum):
    UNKNOWN = -1
    STATUS_UNSPECIFIED = _base.STATUS_UNSPECIFIED
    CREATED = _base.CREATED
    PENDING = _base.PENDING
    IN_PROGRESS = _base.IN_PROGRESS
    COMPLETED = _base.COMPLETED
    FAILED = _base.FAILED
    CANCELED = _base.CANCELED

    @property
    def is_running(self) -> bool:
        return self in (self.IN_PROGRESS, self.PENDING, self.CREATED)

    @property
    def is_succeeded(self) -> bool:
        return self is self.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self in (self.FAILED, self.CANCELED)
