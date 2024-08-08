from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main():
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.text_classifications('yandexgpt')

    result = model.run_few_shot(
        "foo",
        task_description="",
        labels=["foo", "bar"]
    )

    for prediction in result:
        print(prediction)

    result = model.run_few_shot(
        "foo",
        task_description="",
        labels=["foo", "bar"],
        samples=[
            {"text": "foo", "label": "bar"},
            {"text": "bar", "label": "foo"},
        ],
    )

    for prediction in result:
        print(prediction)


if __name__ == '__main__':
    main()
