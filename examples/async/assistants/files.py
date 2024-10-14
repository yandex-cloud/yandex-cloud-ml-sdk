#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
        service_map={
            'ai-files': 'assistant.api.cloud.yandex.net'
        }
    )

    path = pathlib.Path(__file__).parent / 'example_file'
    file = await sdk.files.upload(path, ttl_days=5, expiration_policy="static")

    print(file)

    await file.update(name='foo', ttl_days=9)
    print(file)

    second = await sdk.files.get(file.id)
    await second.update(name='foo', expiration_policy='since_last_active')

    print(second)

    print(await file.get_url())
    print(await file.download_as_bytes())

    async for file in sdk.files.list():
        print(f"delete file {file}")
        await file.delete()

if __name__ == '__main__':
    asyncio.run(main())
