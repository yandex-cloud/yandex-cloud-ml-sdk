from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk._models.text_embeddings.result import TextEmbeddingsModelResult


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.models.text_embeddings('doc')


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_run(model):
    result = await model.run('hello')

    assert len(result) == len(result.embedding) == 256
    assert result.num_tokens == 3


def test_configure(model):
    model = model.configure()

    with pytest.raises(TypeError):
        model.configure(foo=500)


@pytest.mark.require_env('numpy')
def test_numpy_integration():
    import numpy  # pylint: disable=import-outside-toplevel

    array = (1.0, 2.0, 3.0)

    result = TextEmbeddingsModelResult(
        embedding=array,
        num_tokens=-1,
        model_version='foo'
    )

    assert list(result) == list(array)

    assert (numpy.array(result) == numpy.array(array)).all()

    assert numpy.array(result).dtype == 'float64'
