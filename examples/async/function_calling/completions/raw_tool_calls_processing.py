#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


def calculator(expression: str) -> str:
    print(f'calculator got {expression=}')
    return "-5"


def weather(location: str, date: str) -> str:
    print(f"weather func got {location=} and {date=}")
    return "-10 celsius"


def process_tool_calls(tool_calls) -> dict[str, list[dict]]:
    """
    This function is an example how you could organize
    dispatching of function calls in general case
    """

    function_map = {
        'calculator': calculator,
        'Weather': weather
    }

    result = []
    for tool_call in tool_calls:
        # only functions are available at the moment
        assert tool_call.function

        function = function_map[tool_call.function.name]

        answer = function(**tool_call.function.arguments)  # type: ignore[operator]

        result.append({'name': tool_call.function.name, 'content': answer})

    return {'tool_results': result}


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    calculator_tool = sdk.tools.function(
        name="calculator",
        description="A simple calculator that performs basic arithmetic and @ operations.",
        # parameters could contain valid jsonschema with function parameters types and description
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4').",
                }
            },
            "required": ["expression"],
        }
    )

    # it is imported inside only because yandex-cloud-ml-sdk does not require pydantic by default
    # pylint: disable=import-outside-toplevel
    from pydantic import BaseModel, Field

    class Weather(BaseModel):
        """Getting the weather in specified location for specified date"""

        # It is important to describe all the arguments with a natural language
        location: str = Field(description="Name of the place for fetching weatcher at")
        date: str = Field(description="Date which a user interested in")

    # you could also pass pydantic model to the parameters argument;
    # in this case function name, description and parameters schema would
    # be inferred from pydantic model
    weather_tool = sdk.tools.function(Weather)

    model = sdk.models.completions('yandexgpt')

    # tools must be bound to model object via .configure method and would be used in all
    # model calls from this model object.
    model = model.configure(tools=[calculator_tool, weather_tool], temperature=0)

    for question in ["How much it would be 7@8?", "What is the weather like in Paris at 12 of March?"]:
        # it is required to carefully maintain context for passing tool_results back to the model after function call
        messages: list = [
            {"role": "system", "text": "Please use English language for answer"},
            question
        ]

        result = await model.run(messages)

        # if result object contains tool calls, it would be treated as a tool call history next time
        # you will pass "messages" to a model.
        # if there is no tool calls, it still will be treated as a usual text message with a proper role.
        # NB: result is a shortcut for result[0].alternative in this context.
        messages.append(result)

        if result.tool_calls:
            tool_results = process_tool_calls(result.tool_calls)
            # we adding a special tool results message to a history
            messages.append(tool_results)
            # and running model second time to pass tool results with a context back to model.
            result = await model.run(messages)
        else:
            raise RuntimeError('in this example model should return tool calls every time')

        print(f"Model answer for {question=}:", result.text)


if __name__ == '__main__':
    asyncio.run(main())
