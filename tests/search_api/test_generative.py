from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._models.completions.result import Alternative, GPTModelResult
from yandex_cloud_ml_sdk._search_api.generative.message import GenSearchMessage, messages_to_proto
from yandex_cloud_ml_sdk._search_api.generative.result import GenerativeSearchResult


@pytest.mark.asyncio
async def test_generative_settings(async_sdk: AsyncYCloudML) -> None:
    for field in ('host', 'site', 'url'):
        search = async_sdk.search_api.generative(**{field: 'foo'})
        assert getattr(search.config, field) == ('foo', )

        search = async_sdk.search_api.generative(**{field: ['foo', 'bar']})
        assert getattr(search.config, field) == ('foo', 'bar')

    with pytest.raises(ValueError):
        async_sdk.search_api.generative(host='foo', site='bar')

    search = async_sdk.search_api.generative(host='foo')
    assert search.config.host == ('foo', )
    assert search.config.site is None
    with pytest.raises(ValueError):
        search.configure(site='bar')

    search = search.configure(site='bar', host=None)
    assert search.config.site == ('bar', )
    assert search.config.host is None

    search = search.configure(site=None)
    assert search.config.site is None
    assert search.config.host is None
    assert search.config.url is None
    with pytest.raises(ValueError):
        await search.run('foo')

    with pytest.raises(TypeError):
        search = search.configure(site=123)


@pytest.mark.asyncio
async def test_generative_filters(async_sdk: AsyncYCloudML) -> None:
    for field in ('lang', 'format', 'date'):
        search = async_sdk.search_api.generative(search_filters={field: 'ods'})
        search2 = async_sdk.search_api.generative(search_filters=[{field: 'ods'}])
        assert search.config.search_filters == search2.config.search_filters == ({field: 'ods'}, )

    search = async_sdk.search_api.generative(search_filters=[{'lang': 'bar'}, {'format': 'ods'}])
    assert search.config.search_filters == ({'lang': 'bar'}, {'format': 'ods'})

    for bad_value in (
        {'foo': 'bar'},
        'foo',
        {'format': 'foo'},
        [['foo']]
    ):
        with pytest.raises(ValueError):
            async_sdk.search_api.generative(search_filters=bad_value)

    for format_ in async_sdk.search_api.generative.available_formats:
        async_sdk.search_api.generative(search_filters={'format': format_})


def test_generative_messages_transform() -> None:
    class TextClass:
        @property
        def text(self):
            return 'cls'

    class RoleClass(TextClass):
        @property
        def role(self):
            return 'user'

    gpt_model_result = GPTModelResult(
        alternatives=[
            Alternative(role='user', text='gpt', status=None, tool_calls=None),
            Alternative(role='2', text='2', status=None, tool_calls=None),
        ],
        usage=None,
        model_version=''
    )

    search_result = GenerativeSearchResult(
        role='user',
        text='search',
        fixed_misspell_query=False,
        is_answer_rejected=False,
        is_bullet_answer=False,
        search_queries=(),
        sources=()
    )

    for input_, expected in (
        ([], []),
        # text input
        ('foo',
         [{'text': 'foo', 'role': 1}]),
        # text list input
        (['foo', 'bar'],
         [{'text': 'foo', 'role': 1}, {'text': 'bar', 'role': 1}]),
        # dict input
        ({'text': 'foo'},
         [{'text': 'foo', 'role': 1}]),
        ({'text': 'foo', 'role': 'user'},
         [{'text': 'foo', 'role': 1}]),
        ({'text': 'foo', 'role': 'assistant'},
         [{'text': 'foo', 'role': 2}]),
        ({'text': 'foo', 'role': 'role_user'},
         [{'text': 'foo', 'role': 1}]),
        ({'text': 'foo', 'role': 'role_assistant'},
         [{'text': 'foo', 'role': 2}]),
        # list dict input
        ([{'text': 'foo', 'role': 'user'}, {'text': 'bar', 'role': 'assistant'}],
         [{'text': 'foo', 'role': 1}, {'text': 'bar', 'role': 2}]),
        # class input
        (RoleClass(),
         [{'text': 'cls', 'role': 1}]),
        # mixed input
        ([RoleClass(), 'foo', {'text': 'bar', 'role': 'assistant'}],
         [{'text': 'cls', 'role': 1}, {'text': 'foo', 'role': 1}, {'text': 'bar', 'role': 2}]),
        # other classes
        (gpt_model_result,
         [{'text': 'gpt', 'role': 1}]),
        (search_result,
         [{'text': 'search', 'role': 1}]),
    ):
        messages = messages_to_proto(input_)
        assert len(messages) == len(expected)
        for message, expected_message in zip(messages, expected):
            assert isinstance(message, GenSearchMessage)
            assert message.content == expected_message['text']
            assert message.role == expected_message['role']


def test_generative_messages_fail() -> None:
    class TextClass:
        @property
        def text(self):
            return 'cls'

    for input_ in (
        TextClass(),
        1,
        ['foo', 1],
        {'role': 'user'},
        {'text': 1},
        {'foo': 'bar'},
        int,
        b'foo',
    ):
        with pytest.raises(TypeError):
            messages_to_proto(input_)

    for input_ in (
        {'text': 'foo', 'role': 'nonexisting_role'},
        ['foo', {'text': 'foo', 'role': 'nonexisting_role'}],
    ):
        with pytest.raises(ValueError):
            messages_to_proto(input_)


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_search_simple_run(async_sdk: AsyncYCloudML) -> None:
    search = async_sdk.search_api.generative(site='yandex.cloud')

    result = await search.run('Yandex DataLense')

    assert result.text.startswith('**Yandex DataLens**')
    assert result.role =='assistant'

    assert len(result.sources) > 1
    assert any(s.used for s in result.sources)

    source = result.sources[0]
    assert source.url == 'https://datalens.yandex.cloud/'
    assert not source.used
    assert source.title == 'Yandex DataLens – облачная BI-система'

    assert not result.fixed_misspell_query
    assert not result.is_answer_rejected
    assert not result.is_bullet_answer

    assert len(result.search_queries) == 1
    assert result.search_queries[0].text == 'yandex datalens'
