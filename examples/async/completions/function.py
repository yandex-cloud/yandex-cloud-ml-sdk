#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    # pylint: disable=import-outside-toplevel
    from pydantic import BaseModel, Field

    class Weather(BaseModel):
        """Backend which could fetch weather for some date and location"""

        location: str = Field(description="Name of the place for fetching weatcher at")
        date: str = Field(description="Date which user interested in")

    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    calculator_tool = sdk.tools.function(
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

    weather_tool = sdk.tools.function(
        name='weather',
        parameters=Weather,
    )

    model = sdk.models.completions('yandexgpt')
    model = model.configure(tools=[calculator_tool, weather_tool])

    calculator_result = await model.run("How much it would be 7*8?")
    print(calculator_result.tool_calls)

    weather_result = await model.run("What is the weather like in Paris at 12 of March?")
    print(weather_result.tool_calls)


if __name__ == '__main__':
    asyncio.run(main())
