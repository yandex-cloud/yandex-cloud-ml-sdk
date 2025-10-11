# pylint: disable=no-name-in-module
from __future__ import annotations

from enum import IntEnum

from yandex.cloud.ai.batch_inference.v1.batch_inference_task_pb2 import BatchInferenceTask as ProtoBatchInferenceTask

from yandex_cloud_ml_sdk._types.operation import BaseOperationStatus
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase

_base = ProtoBatchInferenceTask.Status


class BatchTaskStatus(BaseOperationStatus, ProtoEnumBase, IntEnum):
    """
    Enumeration of possible batch task statuses.

    This class represents the various states that a batch inference task can be in
    during its lifecycle. It combines status information from the protobuf definition
    with additional utility methods for status checking.
    """
    #: Unknown status (-1)
    UNKNOWN = -1
    #: Unspecified status from protobuf
    STATUS_UNSPECIFIED = _base.STATUS_UNSPECIFIED
    #: Task has been created
    CREATED = _base.CREATED
    #: Task is pending execution
    PENDING = _base.PENDING
    #: Task is currently being processed
    IN_PROGRESS = _base.IN_PROGRESS
    #: Task has completed successfully
    COMPLETED = _base.COMPLETED
    #: Task has failed
    FAILED = _base.FAILED
    #: Task has been canceled
    CANCELED = _base.CANCELED

    @property
    @doc_from(BaseOperationStatus.is_running)
    def is_running(self) -> bool:
        return self in (self.IN_PROGRESS, self.PENDING, self.CREATED)

    @property
    @doc_from(BaseOperationStatus.is_succeeded)
    def is_succeeded(self) -> bool:
        return self is self.COMPLETED

    @property
    @doc_from(BaseOperationStatus.is_failed)
    def is_failed(self) -> bool:
        return self in (self.FAILED, self.CANCELED)
