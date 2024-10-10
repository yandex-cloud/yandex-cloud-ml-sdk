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

    thread = await sdk.threads.create(name='foo')
    second = await sdk.threads.get(thread.id)

    await thread.write("content")
    await second.write("content2")
    async for message in thread:
        print(message)
        print(message.text)

    async for thread in sdk.threads.list():
        await thread.delete()


if __name__ == '__main__':
    asyncio.run(main())
