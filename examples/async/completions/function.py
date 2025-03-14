#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    tool = sdk.tools.function(
        name="calculator",
        description="A simple calculator that performs basic arithmetic operations.",
        parameters={
            "name": "calculator",
            "description": "A simple calculator that performs basic arithmetic operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4').",
                    }
                },
                "required": ["expression"],
            }
        }
    )

    model = sdk.models.completions('yandexgpt').configure(tools=[tool])

    result = await model.run("How much it would be 7*8?")

    print(result)

    for alternative in result:
        print(alternative.text)


if __name__ == '__main__':
    asyncio.run(main())
