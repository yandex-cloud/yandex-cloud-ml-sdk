#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import json

import pydantic

from yandex_cloud_ml_sdk import AsyncYCloudML


class Venue(pydantic.BaseModel):
    date: str
    place: str


@pydantic.dataclasses.dataclass
class VenueDataclass:
    date: str
    place: str
    name: str


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # NB: for now (24.02.2025) structured output is supported only at release candidate model version.
    model = sdk.models.completions('yandexgpt', model_version='rc')
    text = (
        'The conference will take place from May 10th to 12th, 2023, '
        'at 30 Avenue Corentin Cariou in Paris, France.'
    )

    # We could as model to return data just with json format, model will
    # figure out format by itself:
    model = model.configure(response_format='json')
    result = await model.run([
        {'role': 'system', 'text': 'Extract the date and venue information'},
        {'role': 'user', 'text': text},
    ])
    print('Any JSON:', result[0].text)

    # Now, if you need not just JSON, but a parsed Python structure, you will need to parse it.
    # Be aware that you may need to handle parsing exceptions in case the model returns incorrect json.
    # This could happen, for example, if you exceed the token limit.
    try:
        data = json.loads(result.text)
        print("Parsed JSON:", data)

        bad_text = result.text[:5]
        json.loads(bad_text)
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)

    # You could use not only .run, but .run_stream as well as other methods too:
    print('Any JSON in streaming:')
    async for partial_result in model.run_stream([
        {'role': 'system', 'text': 'Extract the date and venue information'},
        {'role': 'user', 'text': text},
    ]):
        print(f"    {partial_result.text}")

    # NB: For each example, I am trying to make slightly different format to show a difference at print results.
    # We could pass a raw json schema:
    model = model.configure(response_format={
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
    })
    result = await model.run([
        {'role': 'system', 'text': 'Extract the date and venue information'},
        {'role': 'user', 'text': text},
    ])
    print('JSONSchema from raw jsonschema:', result[0].text)

    # Also we could use pydantic.BaseModel descendant to describe JSONSchema for
    # structured output:
    model = model.configure(response_format=Venue)
    result = await model.run([
        {'role': 'system', 'text': 'Extract the date and venue information'},
        {'role': 'user', 'text': text},
    ])
    print('JSONSchema from Pydantic model:', result[0].text)

    # Lastly we could pass pydantic-dataclass:
    assert pydantic.__version__ > "2"
    model = model.configure(response_format=VenueDataclass)
    result = await model.run([
        {'role': 'system', 'text': 'Extract the date and venue information'},
        {'role': 'user', 'text': text},
    ])
    print('JSONSchema from Pydantic dataclass:', result[0].text)


if __name__ == '__main__':
    asyncio.run(main())
