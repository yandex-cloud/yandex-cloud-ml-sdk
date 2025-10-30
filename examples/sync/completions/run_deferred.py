#!/usr/bin/env python3

from __future__ import annotations

import time

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        #folder_id="<YC_FOLDER_ID>",
        #auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt')

    operation = model.configure(temperature=0.5).run_deferred("foo")

    status = operation.get_status()
    while status.is_running:
        time.sleep(5)
        status = operation.get_status()

    result = operation.get_result()
    print(result)

    operation = model.configure().run_deferred("bar")

    result = operation.wait()
    print(result)


if __name__ == '__main__':
    main()
