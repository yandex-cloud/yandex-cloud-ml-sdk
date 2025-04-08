#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.assistants import AutoPromptTruncationStrategy, LastMessagesPromptTruncationStrategy

LABEL_KEY = 'yc-ml-sdk-example'
LABEL_VALUE = 'prompt-truncation-options'


async def new_thread(sdk):
    thread = await sdk.threads.create(labels={LABEL_KEY: LABEL_VALUE})
    await thread.write('hey, how are you?')
    await thread.write('what is your name?')
    return thread


async def delete_labeled_entities(iterator):
    async for entity in iterator:
        if entity.labels and entity.labels.get(LABEL_KEY) == LABEL_VALUE:
            print(f'deleting {entity.__class__.__name__} with id={entity.id!r}')
            await entity.delete()


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    assistant = await sdk.assistants.create(
        'yandexgpt',
        labels={LABEL_KEY: LABEL_VALUE},
        # you could choose value for max_prompt_tokens, default value
        # is 7000 by the time I'm making this example
        max_prompt_tokens=500,
        # default prompt truncation strategy is AutoPromptTruncationStrategy, you could
        # change it as well
        prompt_truncation_strategy=LastMessagesPromptTruncationStrategy(num_messages=10),
    )

    thread = await new_thread(sdk)
    # You could also override prompt trunction options vis custom_* run() parameters:
    run = await assistant.run(
        thread,
        custom_max_prompt_tokens=1,
        custom_prompt_truncation_strategy=AutoPromptTruncationStrategy()
    )
    result = await run
    # This run should be failed because of custom_max_prompt_tokens=1
    assert result.is_failed
    print(f'{result.error=}')

    thread = await new_thread(sdk)
    run = await assistant.run(
        thread,
        custom_prompt_truncation_strategy=LastMessagesPromptTruncationStrategy(num_messages=1)
    )
    result = await run
    assert result.usage
    one_message_input_tokens = result.usage.input_text_tokens

    thread = await new_thread(sdk)
    # NB: 'auto' is a shortcut for AutoPromptTruncationStrategy
    run = await assistant.run(thread, custom_prompt_truncation_strategy='auto')
    result = await run
    assert result.usage
    two_message_input_tokens = result.usage.input_text_tokens

    print('Input tokens used with LastMessagesPromptTruncationStrategy(1) < AutoPromptTruncationStrategy():')
    print(f'    {one_message_input_tokens} < {two_message_input_tokens}')

    await delete_labeled_entities(sdk.assistants.list())
    await delete_labeled_entities(sdk.threads.list())


if __name__ == '__main__':
    asyncio.run(main())
