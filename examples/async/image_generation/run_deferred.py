#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import pathlib

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

    model = sdk.models.image_generation('yandex-art')

    # configuring model for all of future runs
    model = model.configure(width_ratio=1, height_ratio=2, seed=50)

    # simple run
    operation = await model.run_deferred('a red cat')
    result = await operation
    print(result)

    # example with several messages
    operation = await model.run_deferred(['a red cat', 'Miyazaki style'])
    result = await operation
    print(result)

    # run with a several messages and with saving image to file
    path = pathlib.Path('image.jpeg')
    try:
        operation = await model.run_deferred(['a red cat', 'Miyazaki style'])
        result = await operation
        path.write_bytes(result.image_bytes)
    finally:
        return
        # path.unlink(missing_ok=True)

    # example of using yandexgpt and yandex-art models together
    gpt = sdk.models.completions('yandexgpt')
    messages = await gpt.run([
        'you need to create a prompt for a yandexart model',
        'of a cat in a Miyazaki style'
    ])
    print(messages)

    operation = await model.run_deferred(messages)
    result = await operation
    print(result)


if __name__ == '__main__':
    asyncio.run(main())
