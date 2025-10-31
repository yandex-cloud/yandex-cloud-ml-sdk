#!/usr/bin/env python3

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

    model = sdk.models.text_classifiers(model_name='yandexgpt-lite', model_version='rc@tamrap1sjscq6e9flit3p')

    # result will contain predictions with a predefined classes
    # and most powerful prediction will be "mathematics": 0.92
    result = model.run("Vieta's formulas")

    for prediction in result:
        print(prediction)

    print("f{result.input_tokens=}")

if __name__ == '__main__':
    main()
