#!/usr/bin/env python3

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')

    model = sdk.models.completions('yandexgpt').langchain(model_type="chat", timeout=60)

    result = model.invoke(
        [
            HumanMessage(content="hello!"),
            AIMessage(content="Hi there human!"),
            HumanMessage(content="Meow!"),
        ]
    )
    print(result)


if __name__ == '__main__':
    main()
