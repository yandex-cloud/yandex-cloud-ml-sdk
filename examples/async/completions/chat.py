#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.completions('yandexgpt')
    model = model.configure(temperature=0.5)

    messages: list[dict[str, str] | str] = [{'role': 'system', 'text': 'Ты - Аркадий'}]
    while True:
        message = input()
        messages.append(message)
        result = await model.run(messages)
        messages.append(result[0])
        print(result[0].text)


if __name__ == '__main__':
    asyncio.run(main())
