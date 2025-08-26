#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML

SCHEMA = {
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4').",
        }
    },
    "required": ["expression"],
}


def get_model(sdk: YCloudML):
    models = sdk.chat.completions.list()
    i = 0
    print('You have access to the following models:')
    for i, model in enumerate(models):
        print(f"  [{i:2}] {model.uri}")

    raw_number = input(f"Please, input model number from 0 to {i}: ")
    number = int(raw_number)
    return models[number]


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # This is how to create model object
    model = sdk.chat.completions('qwen3-235b-a22b-fp8')
    # But in this example we will get it via .list method
    model = get_model(sdk)

    calculator_tool = sdk.tools.function(
        name="calculator_tool",
        description="A simple calculator that performs basic arithmetic and @ operations.",
        parameters=SCHEMA  # type: ignore[arg-type]
    )
    another_calculator = sdk.tools.function(
        name="another_calculator",
        description="A simple calculator that performs basic arithmetic and % operations.",
        parameters=SCHEMA  # type: ignore[arg-type]
    )

    model = model.configure(
        tools=[calculator_tool, another_calculator],
        temperature=0,
        # auto is equivalent to default
        # tool_choice='auto'
    )

    request = "How much it would be 7@8?"
    result = model.run(request)

    # Model could call the tool, but it depends on many things, for example - model version.
    # Right now I writing this example it does not calling the tool
    print(result)

    # You could configure that you don't want to call any tool
    model = model.configure(tool_choice='none')
    result = model.run(request)
    assert result.status.name == 'FINAL'

    # You could configure the model to always call some tool
    model = model.configure(tool_choice='required')
    result = model.run(request)
    assert result.tool_calls
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].function
    assert result.tool_calls[0].function.name == 'calculator_tool'

    # Or configure to call specific tool
    model = model.configure(tool_choice={'type': 'function', 'function': {'name': 'another_calculator'}})
    # You could pass just a function tool object instead of this big dict
    model = model.configure(tool_choice=another_calculator)
    result = model.run(request)
    assert result.tool_calls
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].function
    assert result.tool_calls[0].function.name == 'another_calculator'


if __name__ == '__main__':
    main()
