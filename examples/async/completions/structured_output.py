#!/usr/bin/env python3

from __future__ import annotations

import asyncio

import pydantic

from yandex_cloud_ml_sdk import AsyncYCloudML


class Venue(pydantic.BaseModel):
    date: str
    place: str


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt')

    text = (
        'The conference will take place from May 10th to 12th, 2023, '
        'at 30 Avenue Corentin Cariou in Paris, France.'
    )
    result = await model.run([
        {'role': 'system', 'text': 'Extract the date and place information'},
        {'role': 'user', 'text': text},
    ])

    print(result[0].text)


if __name__ == '__main__':
    asyncio.run(main())
