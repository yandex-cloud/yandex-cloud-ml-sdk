#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


def create_tools(sdk: AsyncYCloudML):
    # it is imported inside only because yandex-cloud-ml-sdk does not require pydantic by default
    # pylint: disable=import-outside-toplevel
    from pydantic import BaseModel, Field

    calculator_tool = sdk.tools.function(
        name="calculator",
        description="A simple calculator that performs basic arithmetic operations.",
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

    class Weather(BaseModel):
        """Getting the weather in specified location for specified date"""

        # It is important to describe all the arguments with a natural language
        location: str = Field(description="Name of the place for fetching weatcher at")
        date: str = Field(description="Date which a user interested in")

    weather_tool = sdk.tools.function(Weather)

    return [calculator_tool, weather_tool]


def calculator(expression: str) -> str:
    print(f'calculator got {expression=}')
    return "-5"


def weather(location: str, date: str) -> str:
    print(f"weather func got {location=} and {date=}")
    return "-10 celsius"


def process_tool_calls(tool_calls) -> list[dict]:
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

    return result


async def run_on_thread(assistant, thread):
    run = await assistant.run(thread)
    result = await run

    if result.tool_calls:
        tool_results = process_tool_calls(result.tool_calls)
        await run.submit_tool_results(tool_results)

        # run starting to work again after submitting tool results
        # and we need to wait it's results again
        result = await run

    return result


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt', model_version='rc')

    assistant = await sdk.assistants.create(
        model,
        tools=create_tools(sdk)
    )
    thread = await sdk.threads.create()

    try:
        for question in [
            "How much it would be 7 * 8?",
            "What is the weather like in Paris at 12 of March?"
        ]:
            await thread.write(question)
            result = await run_on_thread(assistant, thread)
            print(f'Assistant response on question "{question}": {result.text}')

        print('All of the thread messages:')
        messages = reversed([message async for message in thread])
        for message in messages:
            print(f'    {message.author.role}: {message.text}')
    finally:
        await thread.delete()
        await assistant.delete()


if __name__ == '__main__':
    asyncio.run(main())
