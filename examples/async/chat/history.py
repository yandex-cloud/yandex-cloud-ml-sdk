#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def get_model(sdk: AsyncYCloudML):
    models = await sdk.chat.completions.list()
    i = 0
    print('You have access to the following models:')
    for i, model in enumerate(models):
        print(f"  [{i:2}] {model.uri}")

    raw_number = input(f"Please, input model number from 0 to {i}: ")
    number = int(raw_number)
    return models[number]


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = await get_model(sdk)
    model = model.configure(temperature=0.5)

    context = []
    while True:
        request = input("Please input request for model: ")
        context.append(request)

        chunk = None
        # I am using run_stream here for extra beuty,
        # this is not different from just "run" when we talking about context
        async for chunk in model.run_stream(context):
            print(chunk[0].delta, end="", flush=True)
        print()
        assert chunk  # to please static type checker

        # We are putting model answer to context to send it to the next
        # request;
        # We could use last chunk object because it have ".text" attribute which
        # contains full model answer
        context.append(chunk)


if __name__ == '__main__':
    asyncio.run(main())
