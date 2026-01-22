#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_ai_studio_sdk import YCloudML


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

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
