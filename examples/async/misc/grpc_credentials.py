#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

import grpc

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    # for example
    endpoint = 'api.cloud.yandex.net'
    path = pathlib.Path('<some-local-path>')
    cert = path.read_bytes()
    creds = grpc.ssl_channel_credentials(cert)

    sdk = AsyncYCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
        endpoint=endpoint,
        grpc_credentials=creds,
    )

    model = sdk.models.completions('yandexgpt')

    result = await model.configure(temperature=0.5).run("foo")

    for alternative in result:
        print(alternative)

if __name__ == '__main__':
    asyncio.run(main())
