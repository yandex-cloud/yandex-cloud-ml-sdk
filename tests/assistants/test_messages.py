# pylint: disable=protected-access
from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_message(async_sdk):
    thread = await async_sdk.threads.create()

    message = await async_sdk._messages.create(
        "foo",
        thread_id=thread.id,
        labels={'foo': 'bar'},
    )

    assert message.parts == ('foo', )
    assert message.labels == {'foo': 'bar'}
    assert message.thread_id == thread.id
    assert message.text == 'foo'
    assert message.author.role == 'USER'
    assert message.status.name == 'COMPLETED'

    await thread.delete()


@pytest.mark.allow_grpc
async def test_message_get(async_sdk):
    thread = await async_sdk.threads.create()
    message = await async_sdk._messages.create(
        "foo",
        thread_id=thread.id
    )

    second_message = await async_sdk._messages.get(message_id=message.id, thread_id=thread.id)

    assert message.id == second_message.id

    # I hope is temporary
    assert message is not second_message

    await thread.delete()


@pytest.mark.allow_grpc
async def test_message_list(async_sdk):
    thread = await async_sdk.threads.create()

    for i in range(10):
        await async_sdk._messages.create(
            str(i),
            thread_id=thread.id
        )
    messages = [f async for f in async_sdk._messages.list(thread_id=thread.id)]
    for i, message in enumerate(messages):
        assert message.parts[0] == str(9 - i)

    await thread.delete()


@pytest.mark.allow_grpc
async def test_message_format(async_sdk):
    thread = await async_sdk.threads.create()
    message = await async_sdk._messages.create(
        "foo1",
        thread_id=thread.id
    )
    assert message.role == 'USER'
    assert message.text == 'foo1'

    message = await thread.write({'text': 'foo2', 'role': 'assistant'})
    assert message.role == 'ASSISTANT'
    assert message.text == 'foo2'

    await asyncio.sleep(1)

    message2 = await thread.write(message)
    assert message.role == message2.role
    assert message.text == message2.text
    assert message.created_at != message2.created_at

    await thread.delete()
