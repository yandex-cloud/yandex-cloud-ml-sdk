#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML

LABEL_KEY = 'yc-ml-sdk-example'
PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'
LABELS = {LABEL_KEY: NAME}


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def get_search_index(sdk):
    """
    This function represents getting or creating demo search_index object.

    In real life you will get it any other way that would suit your case.
    """

    for search_index in sdk.search_indexes.list():
        if search_index.labels and search_index.labels.get(LABEL_KEY) == NAME:
            print(f'using {search_index=}')
            break
    else:
        print('no search indexes found, creating new one')
        files = [
            sdk.files.upload(
                local_path(path),
                ttl_days=5,
                expiration_policy="static",
            )
            for path in ['turkey_example.txt', 'maldives_example.txt']
        ]
        operation = sdk.search_indexes.create_deferred(files, labels=LABELS)
        search_index = operation
        print(f'new {search_index=}')

        for file in files:
            file.delete()

    return search_index


def delete_labeled_entities(iterator):
    """
    Deletes any entities from given iterator which have .labels attribute
    with `labels[LABEL_KEY] == NAME`
    """

    for entity in iterator:
        if entity.labels and entity.labels.get(LABEL_KEY) == NAME:
            print(f'deleting {entity.__class__.__name__} with id={entity.id!r}')
            entity.delete()


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging(log_level='WARNING')

    search_index = get_search_index(sdk)
    thread = sdk.threads.create(labels=LABELS)

    tool = sdk.tools.search_index(search_index)
    assistant = sdk.assistants.create('yandexgpt', tools=[tool], labels=LABELS)

    # Look, if you don't pass a call strategy to a SearchIndex, it is 'always' use by-default
    assert tool.call_strategy is None
    assert assistant.tools[0].call_strategy.value == 'always'  # type: ignore[attr-defined]

    # First of all we are using request which will definitely find something
    search_query = local_path('search_query.txt').read_text().splitlines()[0]
    thread.write(search_query)
    run = assistant.run(thread)
    result = run.wait()
    # NB: citations says if index were used or not
    assert len(result.citations) > 0
    print(f'If you are using "always" call_strategy, it returns {len(result.citations)>0=} citations from search index')

    # Now we will use a search index, which will be used only if it asked to
    tool_with_call_strategy = sdk.tools.search_index(
        search_index,
        call_strategy={
            'type': 'function',
            'function': {'name': 'guide', 'instruction': 'use this only if you are asked to look in the guide'}
        }
    )
    assistant_with_call_strategy = sdk.assistants.create(
        sdk.models.completions('yandexgpt', model_version='rc'),
        tools=[tool_with_call_strategy],
        labels=LABELS
    )

    thread.write(search_query)
    run = assistant_with_call_strategy.run(thread)
    result = run.wait()
    # NB: citations says if index were used or not
    assert len(result.citations) == 0
    print(
        'When you are using special call_strategy and model decides not to use search index according '
        f'to call_strategy instruction, it returns {len(result.citations)>0=} citations from search index'
    )

    thread.write(f"Look at the guide, please: {search_query}")
    run = assistant_with_call_strategy.run(thread)
    result = run.wait()
    # NB: citations says if index were used or not
    assert len(result.citations) > 0
    print(
        'When you are using special call_strategy and model decides to use search index according '
        f'to call_strategy instruction, it returns {len(result.citations)>0=} from search index'
    )

    # we will delete all assistant and threads created in this example
    # to not to increase chaos level, but not the search index, because
    # index creation is a slow operation and could be re-used in this
    # example next run
    delete_labeled_entities(sdk.assistants.list())
    delete_labeled_entities(sdk.threads.list())


if __name__ == '__main__':
    main()
