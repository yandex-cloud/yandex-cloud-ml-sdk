#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

import grpc

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    cert_path = pathlib.Path('/etc/ssl/certs/YandexInternalRootCA.pem')
    cert = cert_path.read_bytes()
    sdk = AsyncYCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
        service_map={
            'ai-foundation-models': 'localhost:8889'
        },
        grpc_credentials=grpc.ssl_channel_credentials(root_certificates=cert),
    )

    print(await sdk.datasets.completions.create(upload_format="foo", timeout=5))


if __name__ == '__main__':
    asyncio.run(main())
