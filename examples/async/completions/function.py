#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


def calculator(expression: str) -> str:
    print(f'calculator got {expression=}')
    return "-5"


def weather(location: str, date: str) -> str:
    print(f"weather func got {location=} and {date=}")
    return "-300"


def process_tool_calls(tool_calls) -> list[dict]:
    function_map = {
        'calculator': calculator,
        'weather': weather
    }

    result = []
    for tool_call in tool_calls:
        # only functions are available at the moment
        assert tool_call.function

        function = function_map[tool_call.function.name]

        answer = function(**tool_call.function.arguments)

        result.append({'name': tool_call.function.name, 'content': answer})

    return {'tool_results': result}


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
            "description": "A simple calculator that performs basic arithmetic and @ operations.",
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
    model = model.configure(tools=[calculator_tool, weather_tool], temperature=0)

    for question in ["How much it would be 7@8?", "What is the weather like in Paris at 12 of March?"]:
        messages = [question]
        result = await model.run(messages)

        # if there are tool calls in result, we need to add it to message history
        # for a context support anyway
        messages.append(result)

        if result.tool_calls:
            tool_results = process_tool_calls(result.tool_calls)
            # we adding a special tool results message to a history
            messages.append(tool_results)
            # and running model second time
            result = await model.run(messages)
        else:
            raise RuntimeError('in this example model should return tool calls every time')

        print(f"Model answer for {question=}:", result.text)

if __name__ == '__main__':
    asyncio.run(main())
