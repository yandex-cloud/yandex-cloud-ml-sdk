#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pprint

from yandex_cloud_ml_sdk import AsyncYCloudML


async def get_model(sdk: AsyncYCloudML):
    models = await sdk.chat.completions.list()
    i = 0
    print('You have access to the following models:')
    for i, model in enumerate(models):
        print(f"  [{i:2}] {model.uri}")

    raw_number = input(f"Please, input model number from 0 to {i}: ")
    number = int(raw_number)
    return models[number]


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncYCloudML(
    )

    print(sdk._folder_id)
    print(sdk._client._auth_provider)
    # sdk.setup_default_logging()
    # res = sdk.chat.completions.list()
    # print(res)


if __name__ == '__main__':
    asyncio.run(main())
