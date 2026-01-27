#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pprint

from yandex_ai_studio_sdk import AsyncAIStudio


async def get_model(sdk: AsyncAIStudio):
    models = await sdk.chat.completions.list()
    i = 0
    print('You have access to the following models:')
    for i, model in enumerate(models):
        print(f"  [{i:2}] {model.uri}")

    raw_number = input(f"Please, input model number from 0 to {i}: ")
    number = int(raw_number)
    return models[number]


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    # This is how to create model object
    model = sdk.chat.completions('qwen3-235b-a22b-fp8')
    # But in this example we will get it via .list method
    model = await get_model(sdk)

    request = "How to calculate the Hirsch index in O(N)"

    model = model.configure(temperature=0.5)

    result = await model.run(request)

    print('You could inspect the fields which have the result structure:')
    pprint.pprint(result)
    print('\n')

    print('Or just access the "text/content" field')
    print(result.text)

    # NB: text and content is a synonyms
    assert result.text == result.content

    model = model.configure(max_tokens=10)
    result = await model.run(request)
    assert result.finish_reason.name == 'LENGTH'
    # status field is a synonym for finish_reason, but with names consistent with
    # another parts ofr yandex_ai_studio_sdk
    assert result.status.name == 'TRUNCATED_FINAL'


if __name__ == '__main__':
    asyncio.run(main())
