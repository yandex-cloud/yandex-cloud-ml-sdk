#!/usr/bin/env python3

from __future__ import annotations

import time

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
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
