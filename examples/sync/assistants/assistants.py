#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    assistant = sdk.assistants.create(
        'yandexgpt',
        ttl_days=1,
        expiration_policy='static',
        temperature=0.5,
        max_prompt_tokens=50,
    )
    print(f"{assistant=}")

    assistant2 = sdk.assistants.get(assistant.id)
    print(f"same {assistant2=}")

    assistant2.update(model='yandexgpt-lite', name='foo', max_tokens=5)
    print(f"updated {assistant2=}")

    for version in assistant.list_versions():
        print(f"assistant {version=}")

    for assistant in sdk.assistants.list():
        print(f"deleting {assistant=}")

        assistant.delete()



if __name__ == '__main__':
    main()
