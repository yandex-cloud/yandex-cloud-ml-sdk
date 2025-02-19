#!/usr/bin/env python3
# pylint: disable=duplicate-code

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = sdk.models.text_classifiers("yandexgpt").configure(
        task_description="определи тип интента",
        labels=[
            "перевод",
            "будильник",
            "погода"
        ],
    )

    # result will be "погода": 1.0
    result = await model.run('переведи на английский "какая погода в лондоне?"')

    for prediction in result:
        print(prediction)

    model = model.configure(
        task_description="определи тип интента",
        labels=[
            "перевод",
            "будильник",
            "погода"
        ],
        samples=[
            {"text": "поставь будильник", "label": "будильник"},
            {"text": "погода на завтра", "label": "погода"},
            {"text": 'переведи фразу "поставь будильник"', "label": "перевод"},
        ]
    )

    # But with the given samples result will change to a "перевод": 0.99
    result = await model.run('переведи на английский "какая погода в лондоне?"')

    for prediction in result:
        print(prediction)


if __name__ == '__main__':
    asyncio.run(main())
