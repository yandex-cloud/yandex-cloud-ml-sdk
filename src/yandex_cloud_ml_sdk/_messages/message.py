# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any

from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Message as ProtoMessage

from yandex_cloud_ml_sdk._types.resource import BaseResource


@dataclasses.dataclass(frozen=True)
class Message(BaseResource):
    thread_id: str
    created_by: str
    created_at: datetime
    labels: dict[str, str] | None
    parts: list[Any]

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoMessage) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto)
        parts: list[Any] = []

        for part in proto.content.content:
            if hasattr(part, 'text'):
                parts.append(part.text.content)
            else:
                raise NotImplementedError(
                    'messages with non-string content are not supported in this SDK version'
                )

        kwargs['parts'] = parts

        return kwargs
