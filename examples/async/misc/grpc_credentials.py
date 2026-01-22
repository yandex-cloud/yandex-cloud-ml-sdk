#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncAIStudio


async def main() -> None:
    # for example
    endpoint = 'api.cloud.yandex.net'
    path = 'ca/bundle/path.pem'

    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        endpoint=endpoint,
        verify=path,
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )

    model = sdk.models.completions('yandexgpt')

    result = await model.configure(temperature=0.5).run("foo")

    for alternative in result:
        print(alternative)

if __name__ == '__main__':
    asyncio.run(main())
