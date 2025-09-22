#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def get_model(sdk: YCloudML):
    models = sdk.chat.completions.list()
    i = 0
    print('You have access to the following models:')
    for i, model in enumerate(models):
        print(f"  [{i:2}] {model.uri}")

    raw_number = input(f"Please, input model number from 0 to {i}: ")
    number = int(raw_number)
    return models[number]


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


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # This is how to create model object
    model = sdk.chat.completions('qwen3-235b-a22b-fp8')
    # But in this example we will get it via .list method
    model = get_model(sdk)

    calculator_tool = sdk.tools.function(
        name="calculator",
        description=(
            "A simple calculator that performs basic arithmetic and @ operations; "
            "call it on ANY arithmetic questions"
        ),
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
        },
        strict=True,
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

    # tools must be bound to model object via .configure method and would be used in all
    # model calls from this model object.
    model = model.configure(
        tools=[calculator_tool, weather_tool],
        temperature=0,
    )

    for question in [
        "How much it would be 7@8?",
        "What is the weather like in Paris at 12 of March?"
    ]:
        # it is required to carefully maintain context for passing tool_results back to the model after function call
        messages: list = [
            {"role": "system", "text": "Please use English language for answer"},
            question
        ]

        while True:
            tool_results = []
            tool_calls = []

            for chunk in model.run_stream(messages):
                # refer to stream.py example to find out more
                # about .delta attribute
                if chunk[0].delta:
                    print(chunk[0].delta, end="", flush=True)
                if chunk.tool_calls:
                    tool_calls.append(chunk)
                    tool_results.append(process_tool_calls(chunk.tool_calls))

            # If there was tool calls, we should put it and it's answer into
            # context array;
            # Otherwise we exiting the loop
            messages.extend(tool_calls)
            messages.extend(tool_results)
            if not tool_results:
                print()
                break


if __name__ == '__main__':
    main()
