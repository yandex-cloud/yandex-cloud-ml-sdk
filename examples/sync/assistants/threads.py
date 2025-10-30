#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        #folder_id="<YC_FOLDER_ID>",
        #auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    thread = sdk.threads.create(name=NAME, ttl_days=5, expiration_policy="static")
    print(f"new {thread=}")

    second = sdk.threads.get(thread.id)
    print(f"same as first, {second=}")
    second.update(ttl_days=9)
    print(f"with updated epiration config, {second=}")

    # You could pass string
    thread.write("content")
    # {"text": str, "role": str} dict
    message2 = second.write({"text": "content2", "role": "ASSISTANT"})
    # or any object which have .text and .role attributes, like a Message object
    # from assistants
    second.write(message2)

    print("and now we could read it:")
    for message in thread:
        print(f"    {message=}")
        print(f"    {message.text=}")
        # Also every message could have TRUNCATED or FILTERED_CONTENT status
        print(f"    {message.status.name=}\n")

    for thread in sdk.threads.list():
        if thread.name == NAME:
            print(f"deleting thread {thread=}")
            thread.delete()


if __name__ == '__main__':
    main()
