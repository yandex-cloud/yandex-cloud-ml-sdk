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

    expiration = {'ttl_days': 6, 'expiration_policy': 'static'}
    assistant = await sdk.assistants.create(
        'yandexgpt',
        temperature=0.5,
        max_prompt_tokens=50,
        **expiration
    )
    print('assistant: ', assistant)
    thread = await sdk.threads.create(name='foo', **expiration)
    print('thread: ', thread)

    await thread.write("hi! how are you")
    run = await assistant.run_stream(thread)
    async for event in run:
        print('event:', event)

    await thread.write("how is your name?")
    run = await assistant.run(thread)
    result = await run
    print('run result:', result)

    async for assistant in sdk.assistants.list():
        await assistant.delete()



if __name__ == '__main__':
    asyncio.run(main())
