#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncYCloudML(
        #folder_id="<YC_FOLDER_ID>",
        #auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt')
    model = model.configure(temperature=0.5)

    messages: list = [{'role': 'system', 'text': 'Ты - Аркадий'}]
    while True:
        message = input()
        messages.append(message)
        result = await model.run(messages)
        messages.append(result[0])
        print(result[0].text)


if __name__ == '__main__':
    asyncio.run(main())
