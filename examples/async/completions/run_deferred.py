#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.completions('yandexgpt')

    operation = await model.configure(temperature=0.5).run_deferred("foo")

    status = await operation.get_status()
    while status.is_running:
        await asyncio.sleep(5)
        status = await operation.get_status()

    result = await operation.get_result()
    print(result)

    operation = await model.configure().run_deferred("bar")

    result = await operation.wait()
    print(result)


if __name__ == '__main__':
    asyncio.run(main())
