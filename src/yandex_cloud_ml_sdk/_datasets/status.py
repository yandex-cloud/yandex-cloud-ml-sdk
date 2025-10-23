from __future__ import annotations

import enum

# pylint: disable=no-name-in-module
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetInfo


class DatasetStatus(enum.IntEnum):
    """
    Enumeration representing the status of a dataset.

    The statuses correspond to the different states a dataset can be in during its lifecycle.
    """
    #: the status of the dataset is unknown; this is typically used as a fallback when the status cannot be determined
    UNKNOWN = -1
    #: the status has not been specified; this is often used as a default value when creating or initializing a dataset
    STATUS_UNSPECIFIED = DatasetInfo.Status.STATUS_UNSPECIFIED
    #: the dataset is in a draft state; this means it is still being created or modified
    DRAFT = DatasetInfo.Status.DRAFT
    #: the dataset is currently undergoing validation
    VALIDATING = DatasetInfo.Status.VALIDATING
    #: the dataset is ready for use; it has passed all necessary validations and can be utilized in operations
    READY = DatasetInfo.Status.READY
    #: the dataset is considered invalid; this may occur if it fails validation
    INVALID = DatasetInfo.Status.INVALID
    #: the dataset is in the process of being deleted
    DELETING = DatasetInfo.Status.DELETING

    @classmethod
    def _from_str(cls, string: str) -> DatasetStatus:
        number = DatasetInfo.Status.Value(string.upper())
        return cls._from_proto(number)

    @classmethod
    def _from_proto(cls, proto: int) -> DatasetStatus:
        try:
            return cls(proto)
        except ValueError:
            return cls(-1)
