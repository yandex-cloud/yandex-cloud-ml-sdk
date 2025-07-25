#!/usr/bin/env python3

from __future__ import annotations

import json
import pathlib

import pydantic

from yandex_cloud_ml_sdk import YCloudML

PATH = pathlib.Path(__file__)
LABEL_KEY = 'yc-ml-sdk-example'
LABEL_VALUE = f'example-{PATH.parent.name}-{PATH.name}'
LABELS = {LABEL_KEY: LABEL_VALUE}

TEXT = (
    'The conference will take place from May 10th to 12th, 2023, '
    'at 30 Avenue Corentin Cariou in Paris, France.'
)
SCHEMA = {
    "json_schema": {
        "properties": {
            "DATE": {
                "title": "Date",
                "type": "string"
            },
            "PLACE": {
                "title": "Place",
                "type": "string"
            }
        },
        "required": ["DATE", "PLACE"],
        "title": "Venue",
        "type": "object"
    }
}


class Venue(pydantic.BaseModel):
    date: str
    place: str


@pydantic.dataclasses.dataclass
class VenueDataclass:
    date: str
    place: str
    name: str


def delete_labeled_entities(iterator):
    for entity in iterator:
        if entity.labels and entity.labels.get(LABEL_KEY) == LABEL_VALUE:
            print(f'deleting {entity.__class__.__name__} with id={entity.id!r}')
            entity.delete()


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging(log_level='WARNING')

    assistant = sdk.assistants.create(
        sdk.models.completions('yandexgpt', model_version='rc'),
        instruction="Extract the date and venue information",
        labels=LABELS,
        # You could pass response format when creating assisntant
        # But to make example more demonstrative I do not do it
        # response_format="json"
    )
    thread = sdk.threads.create(labels=LABELS)

    # First, we running assistant as usual, whiout any response format set:
    thread.write(TEXT)
    run = assistant.run(thread)
    result = run.wait()
    print('Model answer without any response format set:', result.text)

    # You could pass a dict with json schema as response format:
    assistant.update(response_format=SCHEMA)  # type: ignore[arg-type,typeddict-item]
    thread.write(TEXT)
    run = assistant.run(thread)
    result = run.wait()
    print('Json object with passed schema json fields:', result.text)

    # You could set assistant to return any json without schema
    assistant.update(response_format='json')
    thread.write(TEXT)
    run = assistant.run(thread)
    result = run.wait()
    print('Json object with model-determied json fields:', result.text)

    thread.write(TEXT)
    # You could also pass a pydantic model class
    # And you could do it not via overriding assistant settings,
    # but with custom_response_format parameter when creating a run
    run = assistant.run(thread, custom_response_format=Venue)
    result = run.wait()
    print('Json object with run overridden format with pydantic model:', result.text)

    thread.write(TEXT)
    print('Stream json answer with run overridden pydantic dataclass:')
    run = assistant.run_stream(thread, custom_response_format=VenueDataclass)
    event = None
    for event in run:
        if event.status.name != 'DONE':
            print(f'    {event.text}')
        else:
            print(f'Final stream result: {event.text}')

    assert event
    try:
        assert event.text
        data = json.loads(event.text)
        print("Parsed JSON:", data)

        # Note that you should always handle possible parsing errors in case of model
        # will return non-valid json (for example if you exceed the token limit)
        bad_text = event.text[:5]
        json.loads(bad_text)
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)

    # remove any assistants and threads, associated with this example
    delete_labeled_entities(sdk.assistants.list())
    delete_labeled_entities(sdk.threads.list())


if __name__ == '__main__':
    main()
