#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    thread = await sdk.threads.create(name='foo', ttl_days=5, expiration_policy="static")
    print(f"new {thread=}")

    second = await sdk.threads.get(thread.id)
    print(f"same as first, {second=}")
    await second.update(ttl_days=9)
    print(f"with updated epiration config, {second=}")

    message = await thread.write("content")
    message2 = await second.write("content2")
    print(f"hey, we just writed {message=} and {message2} into the thread")

    print("and now we could read it:")
    async for message in thread:
        print(f"    {message=}")
        print(f"    {message.text=}\n")

    async for thread in sdk.threads.list():
        print(f"deleting thread {thread=}")
        await thread.delete()


if __name__ == '__main__':
    asyncio.run(main())
