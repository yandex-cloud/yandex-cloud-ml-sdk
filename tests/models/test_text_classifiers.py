from __future__ import annotations

import time

import pytest


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_run(async_sdk):
    model = async_sdk.models.text_classifiers('cls://yc.fomo.storage.prod.service/yandexgpt/latest')

    result = await model.run('hello')

    assert len(result) == len(result.predictions) == 6
    assert result[0]['label'] == result[0].label == 'computer_science'
    assert result[0]['confidence'] == result[0].confidence
    assert result.input_tokens == 1


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_run_few_shot(async_sdk):
    model = async_sdk.models.text_classifiers('yandexgpt')

    model = model.configure(
        task_description="",
        labels=['foo', 'bar'],
    )

    result = await model.run('hello')

    assert len(result) == len(result.predictions) == 2
    assert result[0]['label'] == result[0].label == 'foo'
    assert result[0].confidence > 0.5

    assert result[1]['label'] == result[1].label == 'bar'
    assert result[1].confidence < 0.5

    model = model.configure(
        samples=[
            {"text": "foo", "label": "bar"},
            {"text": "bar", "label": "foo"},
        ]
    )

    result = await model.run('foo')

    assert len(result) == len(result.predictions) == 2
    assert result[0]['label'] == result[0].label == 'foo'
    assert result[0].confidence < 0.5

    assert result[1]['label'] == result[1].label == 'bar'
    assert result[1].confidence > 0.5

    assert hasattr(result, 'input_tokens')

@pytest.mark.asyncio
async def test_configure(async_sdk):
    model = async_sdk.models.text_classifiers('yandexgpt')
    model = model.configure()

    with pytest.raises(TypeError):
        model.configure(foo=500)

    model = model.configure(task_description="")

    with pytest.raises(ValueError, match="Incorrect combination of config values."):
        await model.run('foo')

    model = model.configure(task_description=None, samples=[])

    with pytest.raises(ValueError):
        await model.run('foo')
