#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')

    path = pathlib.Path(__file__).parent / 'example_file'
    file = sdk.files.upload(path, ttl_days=5, expiration_policy="static")
    print(f"created {file=}")

    file.update(name='foo', ttl_days=9)
    print(f"updated {file=}")

    second = sdk.files.get(file.id)
    print(f"just as file {second=}")
    second.update(name='foo', expiration_policy='since_last_active')
    print(f"it keeps update from first instance, {second=}")

    print(f"url for downloading: {file.get_url()=}")
    print(f"getting content {file.download_as_bytes()=}")

    for file in sdk.files.list():
        print(f"deleting {file=}")
        file.delete()

if __name__ == '__main__':
    main()
