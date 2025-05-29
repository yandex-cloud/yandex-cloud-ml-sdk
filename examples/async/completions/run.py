#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
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
