from __future__ import annotations

import enum

# pylint: disable=no-name-in-module
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetInfo


class DatasetStatus(enum.IntEnum):
    UNKNOWN = -1
    STATUS_UNSPECIFIED = DatasetInfo.Status.STATUS_UNSPECIFIED
    DRAFT = DatasetInfo.Status.DRAFT
    VALIDATING = DatasetInfo.Status.VALIDATING
    READY = DatasetInfo.Status.READY
    INVALID = DatasetInfo.Status.INVALID
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
