from __future__ import annotations

from dataclasses import fields

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.search_indexes import (
    HybridSearchIndexType, IndexNormalizationStrategy, ReciprocalRankFusionIndexCombinationStrategy,
    StaticIndexChunkingStrategy, TextSearchIndexType, VectorSearchIndexType
)

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='test_file_path')
def fixture_test_file_path(tmp_path):
    path = tmp_path / 'test_file'
    path.write_bytes(b'test file')
    yield path


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_search_index(async_sdk, test_file_path):
    file = await async_sdk.files.upload(test_file_path)
    operation = await async_sdk.search_indexes.create_deferred(file)
    search_index = await operation.wait()

    search_index2 = await async_sdk.search_indexes.get(search_index.id)
    assert search_index2.id == search_index.id
    # I hope is temporary
    assert search_index2 is not search_index

    assert isinstance(search_index.index_type, TextSearchIndexType)
    assert isinstance(search_index.index_type.chunking_strategy, StaticIndexChunkingStrategy)

    operation = await async_sdk.search_indexes.create_deferred(file.id, index_type=VectorSearchIndexType())
    search_index3 = await operation.wait()
    assert isinstance(search_index3.index_type, VectorSearchIndexType)

    for field, value in (
        ('name', 'name'),
        ('description', 'description'),
        ('labels', {'foo': 'bar'}),
    ):
        assert getattr(search_index, field) is None

        new_search_index = await search_index.update(
            **{field: value}
        )

        assert new_search_index is search_index

        assert getattr(search_index, field) == value

    await file.delete()
    await search_index.delete()


@pytest.mark.allow_grpc
async def test_search_index_deleted(async_sdk, test_file_path):
    file = await async_sdk.files.upload(test_file_path)
    operation = await async_sdk.search_indexes.create_deferred(file)
    search_index = await operation.wait()

    await search_index.delete()

    for method in ('delete', 'update'):
        with pytest.raises(ValueError):
            await getattr(search_index, method)()

    await file.delete()


@pytest.mark.allow_grpc
async def test_search_index_list(async_sdk, test_file_path):
    file = await async_sdk.files.upload(test_file_path)
    operation = await async_sdk.search_indexes.create_deferred(file)
    search_index = await operation.wait()
    created_search_indexes = []
    for i in range(10):
        operation = await async_sdk.search_indexes.create_deferred([file], name=f"s{i}")
        search_index = await operation.wait()
        created_search_indexes.append(search_index)

    present_search_indexes = set()
    search_indexes = [f async for f in async_sdk.search_indexes.list()]
    for search_index in search_indexes:
        present_search_indexes.add(search_index.id)

    for i, search_index in enumerate(created_search_indexes):
        if search_index.id not in present_search_indexes:
            continue

        assert search_index.name == f's{i}'

    for search_index in search_indexes:
        await search_index.delete()

    await file.delete()


@pytest.mark.allow_grpc
async def test_assistant_with_search_index(async_sdk, tmp_path):
    # pylint: disable=too-many-locals
    raw_file = tmp_path / 'file'
    raw_file.write_text('my secret number is 57')

    file = await async_sdk.files.upload(raw_file)
    operation = await async_sdk.search_indexes.create_deferred(file)
    search_index = await operation.wait()
    tool = async_sdk.tools.search_index(search_index)

    assistant = await async_sdk.assistants.create('yandexgpt', tools=[tool])
    thread = await async_sdk.threads.create()
    await thread.write('what is your secret number')

    run = await assistant.run(thread)
    result = await run

    assert result.text == '57'
    citations = result.citations
    assert citations is result.message.citations
    assert len(citations) == 1
    assert len(citations[0].sources) == 1
    source = citations[0].sources[0]
    assert source.text == 'my secret number is 57'

    assert type(source.search_index) is type(search_index)
    for field in fields(source.search_index):
        name = field.name
        value = getattr(source.search_index, name)
        value2 = getattr(search_index, name)
        if name in ('_lock', 'updated_at'):
            assert value != value2
        else:
            assert value == value2

    assert type(source.file) is type(file)
    for field in fields(source.file):
        name = field.name
        value = getattr(source.file, name)
        value2 = getattr(file, name)
        if name in ('_lock', 'expires_at'):
            assert value != value2, name
        else:
            assert value == value2, name

    await search_index.delete()
    await thread.delete()
    await assistant.delete()
    await file.delete()


@pytest.mark.allow_grpc
async def test_hybrid_search_index(async_sdk: AsyncYCloudML, test_file_path):
    file = await async_sdk.files.upload(test_file_path)
    operation = await async_sdk.search_indexes.create_deferred(
        file,
        index_type=HybridSearchIndexType(
            chunking_strategy=StaticIndexChunkingStrategy(
                max_chunk_size_tokens=700,
                chunk_overlap_tokens=300
            ),
            normalization_strategy='L2',
            combination_strategy=ReciprocalRankFusionIndexCombinationStrategy(k=51)
        )
    )
    search_index = await operation.wait()

    assert isinstance(search_index.index_type, HybridSearchIndexType)
    assert isinstance(search_index.index_type.text_search_index, TextSearchIndexType)
    assert isinstance(search_index.index_type.vector_search_index, VectorSearchIndexType)
    assert isinstance(search_index.index_type.vector_search_index.chunking_strategy, StaticIndexChunkingStrategy)
    assert search_index.index_type.vector_search_index.chunking_strategy.max_chunk_size_tokens == 700
    assert search_index.index_type.normalization_strategy == IndexNormalizationStrategy.L2
    assert isinstance(search_index.index_type.combination_strategy, ReciprocalRankFusionIndexCombinationStrategy)
    assert search_index.index_type.combination_strategy.k == 51


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_add_to_search_index(async_sdk, test_file_path):
    file = await async_sdk.files.upload(test_file_path)
    operation = await async_sdk.search_indexes.create_deferred(file)
    search_index = await operation.wait()

    search_index_files = [file async for file in search_index.list_files()]
    assert len(search_index_files) == 1

    file2 = await async_sdk.files.upload(test_file_path)
    operation = await search_index.add_files_deferred(file2)
    new_index_files = await operation
    assert len(new_index_files) == 1

    search_index_files = [file async for file in search_index.list_files()]
    assert len(search_index_files) == 2
