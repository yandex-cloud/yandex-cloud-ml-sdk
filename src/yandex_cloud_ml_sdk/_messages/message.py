# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any

from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Message as ProtoMessage
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import MessageContent

from yandex_cloud_ml_sdk._types.resource import BaseResource

from .base import BaseMessage
from .citations import Citation

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class Author:
    id: str
    role: str


@dataclasses.dataclass(frozen=True)
class Message(BaseMessage, BaseResource):
    thread_id: str
    created_by: str
    created_at: datetime
    labels: dict[str, str] | None
    author: Author
    citations: tuple[Citation, ...]

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoMessage, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)
        parts: list[Any] = []

        for part in proto.content.content:
            if hasattr(part, 'text'):
                parts.append(part.text.content)
            else:
                raise NotImplementedError(
                    'messages with non-string content are not supported in this SDK version'
                )

        kwargs['parts'] = tuple(parts)
        kwargs['author'] = Author(
            role=proto.author.role,
            id=proto.author.id
        )
        raw_citations = proto.citations or ()
        kwargs['citations'] = tuple(
            Citation._from_proto(proto=citation, sdk=sdk)
            for citation in raw_citations
        )

        return kwargs


@dataclasses.dataclass(frozen=True)
class PartialMessage(BaseMessage, BaseResource):
    @classmethod
    def _kwargs_from_message(cls, proto: MessageContent, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)
        parts: list[Any] = []

        # NB: it takes content from another structure other than Message
        for part in proto.content:
            if hasattr(part, 'text'):
                parts.append(part.text.content)
            else:
                raise NotImplementedError(
                    'messages with non-string content are not supported in this SDK version'
                )

        kwargs['parts'] = tuple(parts)
        return kwargs
