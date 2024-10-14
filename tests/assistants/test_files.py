from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='test_file_path')
def fixture_test_file_path(tmp_path):
    path = tmp_path / 'test_file'
    path.write_bytes(b'test file')
    yield path


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_file(async_sdk, test_file_path):
    file = await async_sdk.files.upload(test_file_path)

    content = await file.download_as_bytes()
    assert content == b'test file'

    url = await file.get_url()
    assert url.startswith('https://')

    for field, value in (
        ('name', 'name'),
        ('description', 'description'),
        ('labels', {'foo': 'bar'}),
    ):
        assert getattr(file, field) is None

        new_file = await file.update(
            **{field: value}
        )

        assert new_file is file

        assert getattr(file, field) == value

    await file.delete()


@pytest.mark.allow_grpc
async def test_file_deleted(async_sdk, test_file_path):
    file = await async_sdk.files.upload(test_file_path)
    await file.delete()

    for method in ('delete', 'get_url', 'download_as_bytes', 'update'):
        with pytest.raises(ValueError):
            await getattr(file, method)()


@pytest.mark.allow_grpc
async def test_file_get(async_sdk, test_file_path):
    file = await async_sdk.files.upload(test_file_path)

    second_file = await async_sdk.files.get(file.id)

    assert file.id == second_file.id

    # I hope is temporary
    assert file is not second_file

    await file.delete()


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_file_list(async_sdk, tmp_path):
    paths = []
    for i in range(10):
        path = tmp_path / str(i)
        path.write_text(f'test_file {i}', encoding='utf-8')
        paths.append(path)

    present_files = set()
    files = [f async for f in async_sdk.files.list()]
    for file in files:
        present_files.add(file.id)

    for i, path in enumerate(paths):
        await async_sdk.files.upload(path, name=str(i))

    files = [f async for f in async_sdk.files.list(page_size=3)]

    for file in files:
        if file.id in present_files:
            continue

        content = await file.download_as_bytes()
        content = content.decode('utf-8')
        assert content == f'test_file {file.name}'

    for file in files:
        await file.delete()


@pytest.mark.allow_grpc
async def test_file_expiration(async_sdk, test_file_path):
    with pytest.raises(ValueError):
        await async_sdk.files.upload(test_file_path, ttl_days=5)

    with pytest.raises(ValueError):
        await async_sdk.files.upload(test_file_path, expiration_policy='static')

    file = await async_sdk.files.upload(test_file_path)
    assert file.expiration_config.ttl_days == 7
    assert file.expiration_config.expiration_policy.name == 'SINCE_LAST_ACTIVE'

    file2 = await async_sdk.files.upload(test_file_path, ttl_days=5, expiration_policy="static")
    assert file2.expiration_config.ttl_days == 5
    assert file2.expiration_config.expiration_policy.name == 'STATIC'

    await file.update(ttl_days=3)
    assert file.expiration_config.ttl_days == 3

    await file.update(expiration_policy='static')
    assert file.expiration_config.expiration_policy.name == 'STATIC'

    await file.delete()
    await file2.delete()
