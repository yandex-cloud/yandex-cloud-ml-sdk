#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncAIStudio


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt')

    result = await model.configure(
        temperature=0.5,
    ).run("how to calculate the Hirsch index in O(N)")

    for alternative in result:
        print(alternative.text)

    result = await model.configure(
        temperature=0.5,
        reasoning_mode='enabled_hidden',
    ).run("how to calculate the Hirsch index in O(N)")
    print(result[0].text)


if __name__ == '__main__':
    asyncio.run(main())
