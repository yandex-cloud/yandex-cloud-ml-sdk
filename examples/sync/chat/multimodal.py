#!/usr/bin/env python3

from __future__ import annotations

import base64
import pathlib

from yandex_cloud_ml_sdk import YCloudML


def get_image_base64():
    image_path = pathlib.Path(__file__).parent / 'example.png'
    image_data = image_path.read_bytes()
    image_base64 = base64.b64encode(image_data)
    return image_base64.decode('utf-8')


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        #folder_id="<YC_FOLDER_ID>",
        #auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
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

    result = model.run(request)

    print(result.text)


if __name__ == '__main__':
    main()
