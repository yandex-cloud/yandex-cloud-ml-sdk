from __future__ import annotations

from typing import Any

from yandex_cloud_ml_sdk._models.completions.message import MessageInputType, ProtoMessage, messages_to_proto


def messages_to_json(messages: MessageInputType) -> list[dict[str, Any]]:
    """:meta private:"""
    proto_messages: list[ProtoMessage] = messages_to_proto(messages)
    result: list[dict[str, Any]] = []

    for message in proto_messages:
        if message.HasField('tool_call_list'):
            raise NotImplementedError('tool calling is not implemented')
        if message.HasField('tool_result_list'):
            raise NotImplementedError('tool calling is not implemented')

        result.append({
            "content": message.text,
            "role": message.role,
        })

    return result
