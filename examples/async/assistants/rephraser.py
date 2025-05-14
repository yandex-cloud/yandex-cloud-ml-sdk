#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML

LABEL_KEY = 'yc-ml-sdk-example'
PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def get_search_index(sdk):
    """
    This function represents getting or creating demo search_index object.

    In real life you will get it any other way that would suit your case.
    """

    async for search_index in sdk.search_indexes.list():
        if search_index.labels and search_index.labels.get(LABEL_KEY) == NAME:
            print(f'using {search_index=}')
            break
    else:
        print('no search indexes found, creating new one')
        file = await sdk.files.upload(
            local_path('turkey_example.txt')
        )
        operation = await sdk.search_indexes.create_deferred(file, labels={LABEL_KEY: NAME})
        search_index = await operation
        print(f'new {search_index=}')

        await file.delete()

    return search_index


async def delete_labeled_entities(iterator):
    """
    Deletes any entities from given iterator which have .labels attribute
    with `labels[LABEL_KEY] == NAME`
    """

    async for entity in iterator:
        if entity.labels and entity.labels.get(LABEL_KEY) == NAME:
            print(f'deleting {entity.__class__.__name__} with id={entity.id!r}')
            await entity.delete()


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging(log_level='WARNING')

    search_index = await get_search_index(sdk)
    labels = {LABEL_KEY: NAME}

    # search index tool without rephraser
    tool = sdk.tools.search_index(search_index)

    # search index tool with rephraser;
    # there is few identical ways to define rephraser:
    ## will use the default `gpt://<folder_id>/rephraser/latest` rephraser
    tool_with_rephraser = sdk.tools.search_index(search_index, rephraser=True)
    ## will use `gpt://<folder_id>/<name>/latest`
    tool_with_rephraser = sdk.tools.search_index(search_index, rephraser='rephraser')
    ## will use custom rephraser object you passed
    rephraser = sdk.tools.rephraser('rephraser', model_version='latest')
    tool_with_rephraser = sdk.tools.search_index(search_index, rephraser=rephraser)

    assistant_wo_rephraser = await sdk.assistants.create('yandexgpt', labels=labels, tools=[tool])
    assistant_with_rephraser = await sdk.assistants.create('yandexgpt', labels=labels, tools=[tool_with_rephraser])

    # NB: Next code just runs assistants with and without rephraser
    # and just shows rephraser effect;
    # If something not clear to you, refer to another assistants examples.
    thread = await sdk.threads.create(labels=labels)

    async def run(query, rephrase: bool) -> None:
        assistant = assistant_with_rephraser if rephrase else assistant_wo_rephraser

        await thread.write(query)
        run = await assistant.run(thread)
        result = await run

        print(f"Question: {query}")
        preposition = 'with' if rephrase else 'without'
        print(f"Answer {preposition} rephraser:\n    {result.text!r}")
        print()

    await run('Куда yбежать?', rephrase=False)  # 1
    await run('Гиде атттапыриццца?', rephrase=False)  # 2
    await run('Где отдохнуть?', rephrase=False)  # 3
    await run('Куда сбежать?', rephrase=False)  # 4

    # Note that #1 and #2 gave the stupid answers, but after
    # we gave "normal" questions in #3 and #4,
    # #1 and #2 with rephraser will give normal answers:
    await run('Куда убежать?', rephrase=True)
    await run('Гиде атттапыриццца?', rephrase=True)

    # we will delete all assistant and threads created in this example
    # to not to increase chaos level, but not the search index, because
    # index creation is a slow operation and could be re-used in this
    # example next run
    await delete_labeled_entities(sdk.assistants.list())
    await delete_labeled_entities(sdk.threads.list())


if __name__ == '__main__':
    asyncio.run(main())
