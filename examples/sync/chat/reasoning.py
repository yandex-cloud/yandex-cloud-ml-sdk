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


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # This is how to create model object
    model = sdk.chat.completions('qwen3-235b-a22b-fp8')
    # But in this example we will get it via .list method
    model = get_model(sdk)

    request = "What it would be 11!?"

    model = model.configure(temperature=0, reasoning_mode='medium')

    result = model.run(request)
    print(f"Request: {request}")
    print(f"Reasoinig text: {result.reasoning_text}")
    print(f"Result text: {result.text}")

    print()
    print(f"Streaming request: {request}")

    model = model.configure(reasoning_mode='high')
    reasoning_started = False
    result_started = False

    for chunk in model.run_stream(request):
        delta: str | None = None
        # NB: there is very important difference between reasoning_delta and reasoning_text,
        # like chunk.text/chunk.delta, look into stream.py example file for details
        if delta := chunk.choices[0].reasoning_delta:
            if not reasoning_started:
                print('Streaming reasoning text: ')

            reasoning_started = True

        elif delta := chunk.choices[0].delta:
            if not result_started:
                print()
                print('Streaming result text: ')
            result_started = True

        if delta:
            print(delta, end="", flush=True)

    # you could reset to default reasoning mode
    model = model.configure(reasoning_mode=None)
    result = model.run(request)
    print(f"Reasoinig text with default resoning mode: {result.reasoning_text}")


if __name__ == '__main__':
    main()
