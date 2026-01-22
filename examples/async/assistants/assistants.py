#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncYCloudML


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncYCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
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
