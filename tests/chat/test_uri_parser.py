import pytest

pytestmark = pytest.mark.asyncio

@pytest.fixture(name="models_fixture")
def raw_models_fixture():
    return [
        {'id': 'gpt://test/alice-model/v2@12', 'object': 'model', 'owned_by': 'alice', 'created': 0},
        {'id': 'gpt://test/alice-model/v1@324', 'object': 'model', 'owned_by': 'alice', 'created': 0},
        {'id': 'gpt://test/bob-model/v2', 'object': 'model', 'owned_by': 'bob', 'created': 0},
        {'id': 'gpt://test/alice-model/v2@fcds', 'object': 'model', 'owned_by': 'bob', 'created': 0},
        {'id': 'gpt://test/alice-model/v2@213', 'object': 'model', 'owned_by': 'alice', 'created': 0},
    ]

@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_completion_uri_parser(async_sdk):
    models = await async_sdk.chat.completions.list()

    assert len(models) != 0

    model = models[0]

    assert model.owner is not None
    assert model.name is not None
    assert model.version is not None
    assert model.fine_tuned is not None

@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_text_embeddings_uri_parser(async_sdk):
    models = await async_sdk.chat.text_embeddings.list()

    assert len(models) != 0

    model = models[0]

    assert model.owner is not None
    assert model.name is not None
    assert model.version is not None
    assert model.fine_tuned is not None


async def test_filter(async_sdk, monkeypatch, models_fixture):
    completions = async_sdk.chat.completions

    async def fake_fetch_raw_models(*_):
        return models_fixture

    monkeypatch.setattr(completions, "_fetch_raw_models", fake_fetch_raw_models.__get__(completions))

    filters = {'owner': 'alice', 'version': 'v2', 'fine_tuned': True}
    res = await completions.list(filters=filters)
    print(res)
    assert isinstance(res, tuple)
    assert all(
        getattr(m, "owner", None) == 'alice' and
        getattr(m, "version", None) == 'v2' and
        getattr(m, "fine_tuned", None) is True
        for m in res
    )
    assert len(res) == 2
