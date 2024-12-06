from __future__ import annotations

from typing import TypeVar

from google.protobuf.message import Message as ProtoMessage

ProtoMessageTypeT = TypeVar('ProtoMessageTypeT', bound=ProtoMessage)
