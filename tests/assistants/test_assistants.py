# pylint: disable=protected-access
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.allow_grpc
async def test_assistant(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt')

    for field, value in (
        ('name', 'name'),
        ('description', 'description'),
        ('labels', {'foo': 'bar'}),
        ('instruction', 'instruction'),
        ('max_prompt_tokens', 50),
    ):
        assert getattr(assistant, field) is None

        new_assistant = await assistant.update(
            **{field: value}
        )
        assert new_assistant is assistant

        assert getattr(assistant, field) == value

    assistant = await async_sdk.assistants.create('yandexgpt')
    model = async_sdk.models.completions('yandexgpt-lite')

    await assistant.update(model=model)
    assert '/yandexgpt-lite/' in assistant.model.uri

    await assistant.update(model='yandexgpt')
    assert '/yandexgpt/' in assistant.model.uri

    assert assistant.model.config.temperature is None
    assert assistant.model.config.max_tokens is None

    await assistant.update(temperature=0.5)
    assert assistant.model.config.temperature == 0.5
    assert assistant.model.config.max_tokens is None

    await assistant.update(max_tokens=50)
    assert assistant.model.config.temperature == 0.5
    assert assistant.model.config.max_tokens == 50

    model = model.configure(max_tokens=100, temperature=1)

    await assistant.update(model=model)
    assert '/yandexgpt-lite/' in assistant.model.uri
    assert assistant.model.config.temperature == 1
    assert assistant.model.config.max_tokens == 100

    await assistant.update(model=model, temperature=0.1)
    assert '/yandexgpt-lite/' in assistant.model.uri
    assert assistant.model.config.temperature == 0.1
    assert assistant.model.config.max_tokens == 100

    await assistant.update(model=model, max_tokens=10)
    assert '/yandexgpt-lite/' in assistant.model.uri
    assert assistant.model.config.temperature == 1
    assert assistant.model.config.max_tokens == 10

    await assistant.delete()


@pytest.mark.allow_grpc
async def test_assistant_zeros(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt')
    assert assistant.model.config.temperature is None

    await assistant.update(temperature=0.5)
    assert assistant.model.config.temperature == 0.5

    await assistant.update(temperature=None)
    # XXX this is a bug:
    assert assistant.model.config.temperature == 0

    await assistant.update(temperature=0)
    assert assistant.model.config.temperature == 0

    assistant2 = await async_sdk.assistants.create('yandexgpt', temperature=0)
    assert assistant2.model.config.temperature == 0

    await assistant2.update(temperature=None)
    # XXX this is a bug:
    assert assistant2.model.config.temperature == 0

    assert assistant.model.config.max_tokens is None

    await assistant.update(max_tokens=50)
    assert assistant.model.config.max_tokens == 50

    # XXX this is not working by because of the backend bug
    # await assistant.update(max_tokens=None)
    # assert assistant.model.config.max_tokens == 0


@pytest.mark.allow_grpc
async def test_assistant_get(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt')

    second_assistant = await async_sdk.assistants.get(assistant.id)

    assert assistant.id == second_assistant.id

    # I hope is temporary
    assert assistant is not second_assistant

    await assistant.delete()


@pytest.mark.allow_grpc
async def test_assistant_list(async_sdk):
    for i in range(10):
        await async_sdk.assistants.create(model='yandexgpt', name=f"t{i}")

    assistants = [f async for f in async_sdk.assistants.list()]
    assistant_names = {t.name for t in assistants}
    assert assistant_names.issuperset({f"t{i}" for i in range(10)})

    for assistant in assistants:
        await assistant.delete()


@pytest.mark.allow_grpc
async def test_assistant_deleted(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt')
    await assistant.delete()

    for method in ('delete', 'update'):
        with pytest.raises(ValueError):
            await getattr(assistant, method)()

    with pytest.raises(ValueError):
        await assistant.delete()


@pytest.mark.allow_grpc
async def test_assistant_expiration(async_sdk):
    with pytest.raises(ValueError):
        await async_sdk.assistants.create(model='yandexgpt', ttl_days=5)

    with pytest.raises(ValueError):
        await async_sdk.assistants.create('yandexgpt', expiration_policy='static')

    assistant = await async_sdk.assistants.create('yandexgpt')
    assert assistant.expiration_config.ttl_days == 7
    assert assistant.expiration_config.expiration_policy.name == 'SINCE_LAST_ACTIVE'

    assistant2 = await async_sdk.assistants.create('yandexgpt', ttl_days=5, expiration_policy="static")
    assert assistant2.expiration_config.ttl_days == 5
    assert assistant2.expiration_config.expiration_policy.name == 'STATIC'

    await assistant.update(ttl_days=3)
    assert assistant.expiration_config.ttl_days == 3

    await assistant.update(expiration_policy='static')
    assert assistant.expiration_config.expiration_policy.name == 'STATIC'

    await assistant.delete()
    await assistant2.delete()


@pytest.mark.allow_grpc
async def test_assistant_versions(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt')

    await assistant.update(name='foo')
    await assistant.update(name='bar', description='baz')

    versions = [v async for v in assistant.list_versions()]

    assert len(versions) == 3

    assert versions[0].assistant.name == 'bar'
    assert versions[0].assistant.description == 'baz'
    assert versions[0].update_mask == ('name', 'description')

    assert versions[1].assistant.name == 'foo'
    assert versions[1].assistant.description is None
    assert versions[1].update_mask == ('name', )

    assert versions[2].assistant.name is None
    assert versions[2].assistant.description is None
    assert versions[2].update_mask == ()

    await assistant.delete()
