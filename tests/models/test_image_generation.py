from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk._messages.message import Message as AssistantMessage
from yandex_cloud_ml_sdk._messages.message import PartialMessage
from yandex_cloud_ml_sdk._models.completions.message import TextMessage
from yandex_cloud_ml_sdk._models.completions.result import Alternative, GPTModelResult
from yandex_cloud_ml_sdk._models.image_generation.message import ImageMessage, ProtoMessage, messages_to_proto


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.models.image_generation('yandex-art')


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_run(model):
    operation = await model.run_deferred(['hello'])
    print(operation.id)
    result = await operation

    assert len(result.image_bytes) > 4

    assert result._repr_jpeg_() == result.image_bytes  # pylint: disable=protected-access


def test_inputs(async_sdk):
    def check_messages(messages, expected):
        assert len(messages) == len(expected)
        for message, expected_message in zip(messages, expected):
            assert isinstance(message, ProtoMessage)
            assert message.text == expected_message

    messages = messages_to_proto('text')
    check_messages(messages, ['text'])

    messages = messages_to_proto(['foo', 'bar'])
    check_messages(messages, ['foo', 'bar'])

    messages = messages_to_proto({'text': 'text', 'weight': 2})
    check_messages(messages, ['text'])
    assert messages[0].weight == 2

    messages = messages_to_proto([{'text': 'foo'}, {'text': 'bar'}])
    check_messages(messages, ['foo', 'bar'])
    assert messages[0].weight == 0

    messages = messages_to_proto(ImageMessage(text='bar'))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 0

    messages = messages_to_proto(ImageMessage(text='bar', weight=2))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 2

    messages = messages_to_proto([
        ImageMessage(text='bar', weight=2),
        ImageMessage(text='foo', weight=1)
    ])
    check_messages(messages, ['bar', 'foo'])
    assert messages[0].weight == 2
    assert messages[1].weight == 1

    messages = messages_to_proto(Alternative(role='foo', text='bar', status=None))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 0

    messages = messages_to_proto(TextMessage(role='foo', text='bar'))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 0

    gpt_model_result = GPTModelResult(
        alternatives=[
            Alternative(role='1', text='1', status=None),
            Alternative(role='2', text='2', status=None),
        ],
        usage=None,
        model_version=''
    )
    messages = messages_to_proto(gpt_model_result)
    check_messages(messages, ['1'])

    assistant_message = AssistantMessage(
        id='1',
        _sdk=async_sdk,
        created_at=None,
        created_by='foo',
        labels=None,
        parts=('a', 'b'),
        author=None,
        thread_id='2',
        citations=(),
    )
    messages = messages_to_proto(assistant_message)
    check_messages(messages, ['a\nb'])

    partial_message = PartialMessage(
        id='1',
        _sdk=async_sdk,
        parts=('y', 'z')
    )
    messages = messages_to_proto(partial_message)
    check_messages(messages, ['y\nz'])

    messages = messages_to_proto(['foo', {'text': 'bar'}, *gpt_model_result, assistant_message, partial_message])
    check_messages(messages, ['foo', 'bar', '1', '2', 'a\nb', 'y\nz'])

    with pytest.raises(TypeError):
        messages_to_proto(1)

    with pytest.raises(TypeError):
        messages_to_proto({})
