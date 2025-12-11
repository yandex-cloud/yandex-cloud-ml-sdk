from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

@pytest.fixture(name="models")
def models_fixture():
    return [
        {'id': 'gpt://test/alice-model/v2@12', 'object': 'model', 'owned_by': 'alice', 'created': 0},
        {'id': 'gpt://test/alice-model/v1@324', 'object': 'model', 'owned_by': 'alice', 'created': 0},
        {'id': 'gpt://test/bob-model/v2', 'object': 'model', 'owned_by': 'bob', 'created': 0},
        {'id': 'gpt://test/alice-model/v2@fcds', 'object': 'model', 'owned_by': 'bob', 'created': 0},
        {'id': 'gpt://test/alice-model/v2@213', 'object': 'model', 'owned_by': 'alice', 'created': 0},
    ]

@pytest.mark.vcr
async def test_completion_uri_parser(async_sdk):
    models = await async_sdk.chat.completions.list()

    assert len(models) != 0

    for model in models:
        assert model.owner is not None
        assert model.name is not None
        assert model.version is not None
        assert model.fine_tuned is not None

@pytest.mark.vcr
async def test_text_embeddings_uri_parser(async_sdk):
    models = await async_sdk.chat.text_embeddings.list()

    assert len(models) != 0

    for model in models:
        assert model.owner is not None
        assert model.name is not None
        assert model.version is not None
        assert model.fine_tuned is not None


async def test_filter(async_sdk, monkeypatch, models):
    completions = async_sdk.chat.completions

    async def fake_fetch_raw_models(*_):
        return models

    monkeypatch.setattr(completions, "_fetch_raw_models", fake_fetch_raw_models.__get__(completions))
    filters = {'name': 'alice-model', 'owner': 'alice', 'version': 'v2', 'fine_tuned': True}

    res = await completions.list(filters=filters)

    assert all((m.owner, m.version, m.fine_tuned) == ('alice', 'v2', True) for m in res)
    assert len(res) == 2


@pytest.mark.asyncio
async def test_filter_with_garbage_field(async_sdk, monkeypatch, models):
    completions = async_sdk.chat.completions

    async def fake_fetch_raw_models(*_):
        return models

    monkeypatch.setattr(
        completions,
        "_fetch_raw_models",
        fake_fetch_raw_models.__get__(completions)
    )

    filters = {'abracadabra': 42}
    with pytest.raises(AttributeError, match="Filtering Error: model object does not have attribute 'abracadabra'"):
        await completions.list(filters=filters)
