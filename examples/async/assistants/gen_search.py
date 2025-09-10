#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    gen_search_tool = sdk.tools.generative_search(
        description="Use search to provide any answer",
    )

    assistant = await sdk.assistants.create('yandexgpt', tools=gen_search_tool)
    thread = await sdk.threads.create()
    await thread.write("how many legs have Sleipnir")
    run = await assistant.run(thread)
    result = await run
    print(f'run {result=} with a run status {result.status.name}')
    print(result.error)

    await assistant.delete()
    await thread.delete()


if __name__ == '__main__':
    asyncio.run(main())
