#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt')

    result = model.configure(
        temperature=0.5,
    ).run("how to calculate the Hirsch index in O(N)")

    for alternative in result:
        print(alternative.text)

    result = model.configure(
        temperature=0.5,
        reasoning_mode='enabled_hidden',
    ).run("how to calculate the Hirsch index in O(N)")
    print(result[0].text)


if __name__ == '__main__':
    main()
