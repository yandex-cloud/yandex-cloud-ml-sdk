#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from langchain_core.messages import AIMessage, HumanMessage

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt').langchain(model_type="chat", timeout=60)

    result = await model.ainvoke(
        [
            HumanMessage(content="hello!"),
            AIMessage(content="Hi there human!"),
            HumanMessage(content="Meow!"),
        ]
    )
    print(result)


if __name__ == '__main__':
    asyncio.run(main())
