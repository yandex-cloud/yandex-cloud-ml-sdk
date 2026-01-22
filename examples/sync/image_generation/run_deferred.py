#!/usr/bin/env python3
from __future__ import annotations

import pathlib

from yandex_ai_studio_sdk import AIStudio


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    model = sdk.models.image_generation('yandex-art')

    # configuring model for all of future runs
    model = model.configure(width_ratio=1, height_ratio=2, seed=50)

    # simple run
    operation = model.run_deferred('a red cat')
    result = operation.wait()
    print(result)

    # example with several messages
    operation = model.run_deferred(['a red cat', 'Miyazaki style'])
    result = operation.wait()
    print(result)

    # run with a several messages and with saving image to file
    path = pathlib.Path('image.jpeg')
    try:
        operation = model.run_deferred(['a red cat', 'Miyazaki style'])
        result = operation.wait()
        path.write_bytes(result.image_bytes)
    finally:
        path.unlink(missing_ok=True)

    # example of using yandexgpt and yandex-art models together
    gpt = sdk.models.completions('yandexgpt')
    messages = gpt.run([
        'you need to create a prompt for a yandexart model',
        'of a cat in a Miyazaki style'
    ])
    print(messages)

    operation = model.run_deferred(messages)
    result = operation.wait()
    print(result)


if __name__ == '__main__':
    main()
