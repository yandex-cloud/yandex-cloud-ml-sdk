#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    assistant = await sdk.assistants.create(
        'yandexgpt',
        temperature=0.5,
        max_prompt_tokens=50,
        ttl_days=6,
        expiration_policy='static',
    )
    print(f'new {assistant=}')

    thread = await sdk.threads.create(
        name='foo',
        ttl_days=6,
        expiration_policy='static',
    )
    message = await thread.write("hi! how are you")
    print(f'new {thread=} with {message=}')

    run = await assistant.run_stream(thread)
    print(f'new stream {run=} on this thread and assistant')
    async for event in run:
        print(f'from stream {event=}')

    message = await thread.write("how is your name?")
    print(f'second {message=}')

    run = await assistant.run(thread)
    print(f'second {run=}')
    result = await run
    print(f'run {result=} with a run status {result.status.name}')

    # you could get access to message status, which is different from run status!
    assert result.message
    print(f'resulting message have status {result.message.status}')
    # and check if message was not censored
    assert result.message.status.name != 'FILTERED_CONTENT'
    # or truncated because of token limits
    assert result.message.status.name != 'TRUNCATED'

    # NB: it doesn't work at the moment at the backend
    # async for run in sdk.runs.list(page_size=10):
    #     print('run:', run)

    async for assistant in sdk.assistants.list():
        await assistant.delete()

    await thread.delete()


if __name__ == '__main__':
    asyncio.run(main())
