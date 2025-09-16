#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import base64
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML


def get_image_base64():
    image_path = pathlib.Path(__file__).parent / 'example.png'
    image_data = image_path.read_bytes()
    image_base64 = base64.b64encode(image_data)
    return image_base64.decode('utf-8')


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # at this moment this is only model which supports image processing
    model = sdk.chat.completions('gemma-3-27b-it')

    request = [
        # this is special kind of multimodal message which allows you to
        # mix image with text data;
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text', 'text': "What is depicted in the following image",
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:image/png;base64,{get_image_base64()}'
                    }
                }
            ]
        }
    ]

    result = await model.run(request)

    print(result.text)


if __name__ == '__main__':
    asyncio.run(main())
