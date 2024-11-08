#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.image_generation('yandex-art')

    # configuring model for all of future runs
    model = model.configure(width_ratio=1, height_ratio=2, seed=50)

    # simple run
    operation = await model.run_deferred('a red cat')
    result = await operation
    print(result)

    # run with a several messages and with saving image to file
    path = pathlib.Path('image.jpeg')
    try:
        operation = await model.run_deferred(['a red cat', 'Miyazaki style'])
        result = await operation
        path.write_bytes(result.image_bytes)
    finally:
        path.unlink(missing_ok=True)

    # example of several messages with a weight
    operation = await model.run_deferred([{'text': 'a red cat', 'weight': 5}, 'Miyazaki style'])
    result = await operation
    print(result)

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
