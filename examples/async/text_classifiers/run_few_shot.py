#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.text_classifiers('yandexgpt').configure(
        task_description="",
        labels=["foo", "bar"]
    )

    result = await model.run("foo")

    for prediction in result:
        print(prediction)

    model = model.configure(
        task_description="",
        labels=["foo", "bar"],
        samples=[
            {"text": "foo", "label": "bar"},
            {"text": "bar", "label": "foo"},
        ],
    )

    result = await model.run("foo")

    for prediction in result:
        print(prediction)


if __name__ == '__main__':
    asyncio.run(main())
