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

    model = get_model(sdk)

    # You could pass any extra query parameters to the model
    # via extra_query configuration parameter
    model = model.configure(temperature=0.5, extra_query={'top_p': 0.2})

    # Note that reconfiguring extra_query will rewrite it's value entirely
    # without any merging
    model = model.configure(extra_query={'top_k': 2})
    print(f"{model.config.extra_query=} {model.config.temperature=}")

    request = 'Say random number from 0 to 10'
    for title, extra_query in (
        ('deterministic', {'top_k': 2, 'top_p': 0.1}),
        ('another deterministic', {'top_k': 2, 'top_p': 0.1}),
        ('more random', {'top_k': 5, 'top_p': 1}),
        ('another more random', {'top_k': 5, 'top_p': 1}),
    ):
        model = model.configure(extra_query=extra_query)
        result = model.run(request)
        print(f"{title} result: {result.text}")

    # Also note that there is no client validation about extra query value at all:
    model = model.configure(extra_query={'foo': 2})
    # This will not fail:
    model.run(request)
    # So, refer to models documentation to find out about extra model parameters


if __name__ == '__main__':
    main()
