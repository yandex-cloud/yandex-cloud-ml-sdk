#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def clear():
    # We are clearing the screen with this ascii combination;
    # it will probably work only at the linux terminals
    print(chr(27) + "[2J")


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

    model = model.configure(temperature=0.5)

    request = "How to calculate the Hirsch index in O(N)"

    chunk = None

    for chunk in model.run_stream(request):
        clear()
        print(f"{request}:")
        print(chunk.text)

        # chunk[0] is a shortcut for chunk.choices[0]:
        choice = chunk[0]
        assert choice == chunk[0] == chunk.choices[0]

        # chunk.text is a shortcut for chunk[0].text:
        assert chunk.text == choice.text

    # There is very important difference between choice.text and
    # choice.delta:
    # * choice.text contains a constantly increasing PREFIX of generated text,
    #   like in other parts of yandex-cloud-ml-sdk
    # * choice.delta contains only newly generated text delta in openai-streaming style
    clear()
    print(f"{request}:")
    for chunk in model.run_stream(request):
        print(chunk[0].delta, end="", flush=True)
    print()

    assert chunk  # to make type checker happy
    # NB: Some of the models have a usage field in the last chunk;
    # qwen3-235b-a22b-fp8 does have it:
    print("{chunk.usage=}")

    model = model.configure(max_tokens=10)
    print('\n')
    print("Showcase for 'length' finish reason:")
    for chunk in model.run_stream(request):
        print(chunk)

    assert chunk.finish_reason.name == 'LENGTH'
    # status field is a synonym for finish_reason, but with names consistent with
    # another parts of yandex_cloud_ml_sdk
    assert chunk.status.name == 'TRUNCATED_FINAL'


if __name__ == '__main__':
    main()
