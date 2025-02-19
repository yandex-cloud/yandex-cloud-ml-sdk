#!/usr/bin/env python3

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt').langchain(model_type="chat", timeout=60)

    for result in model.stream(
        [
            HumanMessage(content="hello!"),
            AIMessage(content="Hi there human!"),
            HumanMessage(content="Meow!"),
        ]
    ):
        print(result)


if __name__ == '__main__':
    main()
