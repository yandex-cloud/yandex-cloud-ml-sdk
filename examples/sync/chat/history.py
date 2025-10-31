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
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    model = get_model(sdk)
    model = model.configure(temperature=0.5)

    context = []
    while True:
        request = input("Please input request for model: ")
        context.append(request)

        chunk = None
        # I am using run_stream here for extra beuty,
        # this is not different from just "run" when we talking about context
        for chunk in model.run_stream(context):
            print(chunk[0].delta, end="", flush=True)
        print()
        assert chunk  # to please static type checker

        # We are putting model answer to context to send it to the next
        # request;
        # We could use last chunk object because it have ".text" attribute which
        # contains full model answer
        context.append(chunk)


if __name__ == '__main__':
    main()
