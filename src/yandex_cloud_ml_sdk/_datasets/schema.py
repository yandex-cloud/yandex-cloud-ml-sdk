# pylint: disable=no-name-in-module
from __future__ import annotations

import ast
from dataclasses import dataclass

from typing_extensions import Self
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetUploadSchema as ProtoDatasetUploadSchema

from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType
from yandex_cloud_ml_sdk._types.schemas import JsonSchemaType


@dataclass(frozen=True)
class DatasetUploadSchema(ProtoBased[ProtoDatasetUploadSchema]):
    task_type: str
    upload_format: str
    raw_schema: str

    @classmethod
    def _from_proto(cls, *, proto: ProtoDatasetUploadSchema, sdk: SDKType) -> Self:
        return cls(
            task_type=proto.task_type,
            upload_format=proto.upload_format,
            raw_schema=proto.schema
        )

    @property
    def json(self) -> JsonSchemaType:
        return ast.literal_eval(self.raw_schema)
