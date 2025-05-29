from __future__ import annotations

from collections.abc import Iterable
from typing import Union

from typing_extensions import TypeAlias
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.gen_search_service_pb2 import GenSearchMessage, Role

from yandex_cloud_ml_sdk._types.message import MessageType, TextMessageProtocol, coerce_to_text_message_dict
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple

MessageInputType: TypeAlias = Union[MessageType, Iterable[MessageType]]

INPUT_ROLES_CORRESPONDENCE = {
    'assistant': Role.ROLE_ASSISTANT,
    'user': Role.ROLE_USER,
}
INPUT_ROLES_CORRESPONDENCE.update({
    f'role_{role}': value
    for role, value in INPUT_ROLES_CORRESPONDENCE.items()
})
AVAILABLE_ROLES = tuple(INPUT_ROLES_CORRESPONDENCE) + tuple(role.upper() for role in INPUT_ROLES_CORRESPONDENCE)


def messages_to_proto(messages: MessageInputType) -> list[GenSearchMessage]:
    result: list[GenSearchMessage] = []

    # This coercing have difficult typing because of TypedDicts
    msgs: tuple[MessageType, ...] = coerce_tuple(
        messages, (str, dict, TextMessageProtocol)  # type: ignore[arg-type]
    )

    for raw_message in msgs:
        message = coerce_to_text_message_dict(raw_message)
        role = message.get('role', 'user')
        if role:
            role = role.lower()

        if not role or role not in INPUT_ROLES_CORRESPONDENCE:
            raise ValueError(f"Unknown role `{role}`, use one of {AVAILABLE_ROLES}")

        role_id = INPUT_ROLES_CORRESPONDENCE[role]
        result.append(
            GenSearchMessage(content=message['text'], role=role_id)
        )

    return result
