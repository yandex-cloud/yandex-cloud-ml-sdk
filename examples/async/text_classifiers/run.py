#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='yc.fomo.storage.prod.service')
    sdk.setup_default_logging()

    model = sdk.models.text_classifiers(model_name='yandexgpt-lite', model_version='rc@tamrap1sjscq6e9flit3p')

    # result will contain predictions with a predefined classes
    # and most powerful prediction will be "mathematics": 0.92
    result = await model.run("Vieta's formulas")

    for prediction in result:
        print(prediction)

    print("f{result.input_tokens=}")

if __name__ == '__main__':
    asyncio.run(main())
