# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any

from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Message as ProtoMessage
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import MessageContent

from yandex_cloud_ml_sdk._types.resource import BaseResource

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class Author:
    id: str
    role: str


@dataclasses.dataclass(frozen=True)
class BaseMessage(BaseResource):
    parts: tuple[Any, ...]

    @property
    def text(self):
        return '\n'.join(
            part for part in self.parts
            if isinstance(part, str)
        )


@dataclasses.dataclass(frozen=True)
class Message(BaseMessage):
    thread_id: str
    created_by: str
    created_at: datetime
    labels: dict[str, str] | None
    author: Author

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

        return kwargs


@dataclasses.dataclass(frozen=True)
class PartialMessage(BaseMessage):
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
