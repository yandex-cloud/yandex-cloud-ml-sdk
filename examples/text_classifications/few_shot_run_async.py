from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main():
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.text_classifications('yandexgpt')

    result = await model.run_few_shot(
        "foo",
        task_description="",
        labels=["foo", "bar"]
    )

    for prediction in result:
        print(prediction)

    result = await model.run_few_shot(
        "foo",
        task_description="",
        labels=["foo", "bar"],
        samples=[
            {"text": "foo", "label": "bar"},
            {"text": "bar", "label": "foo"},
        ],
    )

    for prediction in result:
        print(prediction)


if __name__ == '__main__':
    asyncio.run(main())
