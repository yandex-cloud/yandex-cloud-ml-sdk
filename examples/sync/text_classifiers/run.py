#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.text_classifiers('cls://b1ghsjum2v37c2un8h64/bt14f74au2ap3q0f9ou4')

    # result will contain predictions with a predefined classes
    # and most powerful prediction will be "mathematics": 0.92
    result = model.run("Vieta's formulas")

    for prediction in result:
        print(prediction)


if __name__ == '__main__':
    main()
