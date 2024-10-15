# pylint: disable=protected-access
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_thread(async_sdk):
    thread = await async_sdk.threads.create()

    for field, value in (
        ('name', 'name'),
        ('description', 'description'),
        ('labels', {'foo': 'bar'}),
    ):
        assert getattr(thread, field) is None

        new_thread = await thread.update(
            **{field: value}
        )
        assert new_thread is thread

        assert getattr(thread, field) == value

    await thread.delete()


@pytest.mark.allow_grpc
async def test_thread_get(async_sdk):
    thread = await async_sdk.threads.create()

    second_thread = await async_sdk.threads.get(thread.id)

    assert thread.id == second_thread.id

    # I hope is temporary
    assert thread is not second_thread

    await thread.delete()


@pytest.mark.allow_grpc
async def test_thread_list(async_sdk):
    for i in range(10):
        await async_sdk.threads.create(name=f"t{i}")

    threads = [f async for f in async_sdk.threads.list()]
    thread_names = {t.name for t in threads}
    assert thread_names.issuperset({f"t{i}" for i in range(10)})

    for thread in threads:
        await thread.delete()


@pytest.mark.allow_grpc
async def test_thread_deleted(async_sdk):
    thread = await async_sdk.threads.create()
    await thread.delete()

    for method in ('delete', 'update'):
        with pytest.raises(ValueError):
            await getattr(thread, method)()

    with pytest.raises(ValueError):
        await thread.write('foo')

    with pytest.raises(ValueError):
        async for _ in thread.read():
            pass


@pytest.mark.allow_grpc
async def test_thread_read_write(async_sdk):
    thread = await async_sdk.threads.create()
    for i in range(10):
        await thread.write(str(i))
    messages = [f async for f in thread.read()]

    for i, message in enumerate(messages):
        assert message.parts[0] == str(9 - i)

    await thread.delete()


@pytest.mark.allow_grpc
async def test_thread_expiration(async_sdk):
    with pytest.raises(ValueError):
        await async_sdk.threads.create(ttl_days=5)

    with pytest.raises(ValueError):
        await async_sdk.threads.create(expiration_policy='static')

    thread = await async_sdk.threads.create()
    assert thread.expiration_config.ttl_days == 7
    assert thread.expiration_config.expiration_policy.name == 'SINCE_LAST_ACTIVE'

    thread2 = await async_sdk.threads.create(ttl_days=5, expiration_policy="static")
    assert thread2.expiration_config.ttl_days == 5
    assert thread2.expiration_config.expiration_policy.name == 'STATIC'

    await thread.update(ttl_days=3)
    assert thread.expiration_config.ttl_days == 3

    await thread.update(expiration_policy='static')
    assert thread.expiration_config.expiration_policy.name == 'STATIC'

    await thread.delete()
    await thread2.delete()
