from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.vcr]


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.chat.embeddings('text-search-doc')


async def test_run(model):
    result = await model.run('hello')

    assert result.embedding
    assert len(result.embedding) > 1
    assert len(result) == len(result.embedding)
    assert all(isinstance(value, float) for value in result)


@pytest.mark.require_env('numpy')
async def test_numpy_integration(model):
    import numpy  # pylint: disable=import-outside-toplevel

    result = await model.run('hello')
    array = numpy.array(result)

    assert len(array)

    assert array.dtype == 'float64'
