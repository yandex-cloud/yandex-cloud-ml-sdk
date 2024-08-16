#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.completions('yandexgpt')

    for result in model.configure(temperature=0.5).run_stream("foo"):
        for alternative in result:
            print(alternative)


if __name__ == '__main__':
    main()
