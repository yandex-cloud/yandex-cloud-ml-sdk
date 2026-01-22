# pylint: disable=no-name-in-module
from __future__ import annotations

import ast
from dataclasses import dataclass

from typing_extensions import Self
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetUploadSchema as ProtoDatasetUploadSchema

from yandex_ai_studio_sdk._types.proto import ProtoBased, SDKType
from yandex_ai_studio_sdk._types.schemas import JsonSchemaType


@dataclass(frozen=True)
class DatasetUploadSchema(ProtoBased[ProtoDatasetUploadSchema]):
    """This class represents the schema for uploading datasets."""
    #: the type of task associated with the dataset
    task_type: str
    #: the format in which the dataset is uploaded
    upload_format: str
    #: the raw schema definition in string format
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
        """Get the JSON representation of the raw schema."""
        return ast.literal_eval(self.raw_schema)
