#!/usr/bin/env python3
# pylint: disable=duplicate-code

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
        # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    model = sdk.models.text_classifiers("yandexgpt").configure(
        task_description="определи тип интента",
        labels=[
            "перевод",
            "будильник",
            "погода"
        ],
    )

    # result will be "погода": 1.0
    result = model.run('переведи на английский "какая погода в лондоне?"')

    for prediction in result:
        print(prediction)

    model = model.configure(
        task_description="определи тип интента",
        labels=[
            "перевод",
            "будильник",
            "погода"
        ],
        samples=[
            {"text": "поставь будильник", "label": "будильник"},
            {"text": "погода на завтра", "label": "погода"},
            {"text": 'переведи фразу "поставь будильник"', "label": "перевод"},
        ]
    )

    # But with the given samples result will change to a "перевод": 0.99
    result = model.run('переведи на английский "какая погода в лондоне?"')

    for prediction in result:
        print(prediction)

    print("f{result.input_tokens=}")

if __name__ == '__main__':
    main()
