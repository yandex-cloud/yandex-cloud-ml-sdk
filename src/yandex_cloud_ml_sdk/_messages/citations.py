# pylint: disable=no-name-in-module

from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING

from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Citation as ProtoCitation
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Source as ProtoSource

from yandex_cloud_ml_sdk._files.file import BaseFile
from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.result import BaseResult

from .base import BaseMessage

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class Citation(BaseResult):
    sources: tuple[Source, ...]

    @classmethod
    def _from_proto(cls, proto: ProtoCitation, sdk: BaseSDK) -> Citation:  # type: ignore[override]
        return cls(
            sources=tuple(
                Source._from_proto(proto=source, sdk=sdk)
                for source in proto.sources
            )
        )

class Source(BaseResult):
    @property
    @abc.abstractmethod
    def type(self) -> str:
        pass

    @classmethod
    def _from_proto(cls, proto: ProtoSource, sdk: BaseSDK) -> Source:  # type: ignore[override]
        if proto.HasField('chunk'):
            return FileChunk._from_proto(proto=proto, sdk=sdk)

        return UnknownSource._from_proto(proto=proto, sdk=sdk)


@dataclasses.dataclass(frozen=True)
class FileChunk(Source, BaseMessage):
    search_index: BaseSearchIndex
    file: BaseFile | None

    @property
    def type(self) -> str:
        return 'filechunk'

    @classmethod
    def _from_proto(cls, proto: ProtoSource, sdk: BaseSDK) -> FileChunk | UnknownSource:  # type: ignore[override]
        # pylint: disable=protected-access
        chunk = proto.chunk
        assert chunk

        raw_parts = (part.text.content for part in chunk.content.content)
        parts = tuple(part for part in raw_parts if part)

        search_index = sdk.search_indexes._impl._from_proto(proto=chunk.search_index, sdk=sdk)
        file: BaseFile | None = None

        # NB: at the moment backend always returns non-empty source_file field
        # but in case it deleted, source_file will content empty File structure
        if (
            chunk.HasField('source_file') and
            chunk.source_file and
            chunk.source_file.id
        ):
            file = sdk.files._file_impl._from_proto(proto=chunk.source_file, sdk=sdk)

        return cls(
            search_index=search_index,
            file=file,
            parts=parts,
        )


@dataclasses.dataclass(frozen=True)
class UnknownSource(Source):
    text: str

    @property
    def type(self) -> str:
        return 'unknown'

    @classmethod
    def _from_proto(cls, proto: ProtoSource, sdk: BaseSDK) -> UnknownSource:  # type: ignore[override]
        return cls(
            text="Source's protobuf have unknown fields; try to update yandex-cloud-ml-sdk"
        )
