#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    assistant = await sdk.assistants.create(
        'yandexgpt',
        ttl_days=1,
        expiration_policy='static',
        temperature=0.5,
        max_prompt_tokens=50,
    )
    print(f"{assistant=}")

    assistant2 = await sdk.assistants.get(assistant.id)
    print(f"same {assistant2=}")

    await assistant2.update(model='yandexgpt-lite', name='foo', max_tokens=5)
    print(f"updated {assistant2=}")

    async for version in assistant.list_versions():
        print(f"assistant {version=}")

    async for assistant in sdk.assistants.list():
        print(f"deleting {assistant=}")

        await assistant.delete()



if __name__ == '__main__':
    asyncio.run(main())
