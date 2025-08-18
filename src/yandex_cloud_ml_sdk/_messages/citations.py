# pylint: disable=no-name-in-module

from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING

from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Citation as ProtoCitation
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Source as ProtoSource

from yandex_cloud_ml_sdk._files.file import BaseFile
from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.result import BaseProtoResult

from .base import BaseMessage

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class Citation(BaseProtoResult[ProtoCitation]):
    """
    Represents a citation from search results with multiple sources.

    A citation contains references to one or more sources from search indexes that were used
    to generate or support the content. This is typically used in generative AI responses
    to provide attribution for factual information.
    """
    #: Tuple of Source objects referenced in this citation
    sources: tuple[Source, ...]

    @classmethod
    def _from_proto(cls, proto: ProtoCitation, sdk: BaseSDK) -> Citation:  # type: ignore[override]
        return cls(
            sources=tuple(
                Source._from_proto(proto=source, sdk=sdk)
                for source in proto.sources
            )
        )

class Source(BaseProtoResult[ProtoSource]):
    """
    Abstract base class for citation sources.
    """
    @property
    @abc.abstractmethod
    def type(self) -> str:
        """
        Get the type identifier of this source.
        """
        pass

    @classmethod
    def _from_proto(cls, proto: ProtoSource, sdk: BaseSDK) -> Source:  # type: ignore[override]
        if proto.HasField('chunk'):
            return FileChunk._from_proto(proto=proto, sdk=sdk)

        return UnknownSource._from_proto(proto=proto, sdk=sdk)


@dataclasses.dataclass(frozen=True)
class FileChunk(Source, BaseMessage[ProtoSource]):
    """
    Represents a file chunk citation source.
    """
    #: Search index this chunk belongs to
    search_index: BaseSearchIndex
    #: File this chunk belongs to (optional)
    file: BaseFile | None

    @property
    def type(self) -> str:
        """
        Get the type identifier for file chunks. Always returns 'filechunk'
        """
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
    """
    Represents an unknown citation source type.
    """
    #: Description of the unknown source
    text: str

    @property
    def type(self) -> str:
        """
        Get the type identifier for unknown sources. Always returns 'unknown'.
        """
        return 'unknown'

    @classmethod
    def _from_proto(cls, proto: ProtoSource, sdk: BaseSDK) -> UnknownSource:  # type: ignore[override]
        return cls(
            text="Source's protobuf have unknown fields; try to update yandex-cloud-ml-sdk"
        )
