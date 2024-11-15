#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')

    thread = sdk.threads.create(name='foo', ttl_days=5, expiration_policy="static")
    print(f"new {thread=}")

    second = sdk.threads.get(thread.id)
    print(f"same as first, {second=}")
    second.update(ttl_days=9)
    print(f"with updated epiration config, {second=}")

    message = thread.write("content")
    message2 = second.write("content2")
    print(f"hey, we just writed {message=} and {message2} into the thread")

    print("and now we could read it:")
    for message in thread:
        print(f"    {message=}")
        print(f"    {message.text=}\n")

    for thread in sdk.threads.list():
        print(f"deleting thread {thread=}")
        thread.delete()


if __name__ == '__main__':
    main()
