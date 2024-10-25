#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
        service_map={
            'ai-assistants': 'assistant.api.cloud.yandex.net'
        }
    )

    assistant = await sdk.assistants.create(
        'yandexgpt',
        temperature=0.5,
        max_prompt_tokens=50,
        ttl_days=6,
        expiration_policy='static',
    )
    print('assistant: ', assistant)

    thread = await sdk.threads.create(
        name='foo',
        ttl_days=6,
        expiration_policy='static',
    )
    print('thread: ', thread)

    await thread.write("hi! how are you")
    run = await assistant.run_stream(thread)
    async for event in run:
        print('event:', event)

    await thread.write("how is your name?")
    run = await assistant.run(thread)
    result = await run
    print('run result:', result)

    run = await sdk.runs.get_last_by_thread(thread)
    print('last run:', run)

    async for run in sdk.runs.list(page_size=10):
        print('run:', run)

    async for assistant in sdk.assistants.list():
        await assistant.delete()



if __name__ == '__main__':
    asyncio.run(main())
