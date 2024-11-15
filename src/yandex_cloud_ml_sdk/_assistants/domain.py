# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterable, Iterator

from yandex.cloud.ai.assistants.v1.assistant_pb2 import Assistant as ProtoAssistant
from yandex.cloud.ai.assistants.v1.assistant_service_pb2 import (
    CreateAssistantRequest, GetAssistantRequest, ListAssistantsRequest, ListAssistantsResponse
)
from yandex.cloud.ai.assistants.v1.assistant_service_pb2_grpc import AssistantServiceStub

from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel
from yandex_cloud_ml_sdk._tools.tool import BaseTool
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .assistant import Assistant, AssistantTypeT, AsyncAssistant
from .utils import get_completion_options, get_prompt_trunctation_options


class BaseAssistants(BaseDomain, Generic[AssistantTypeT]):
    _assistant_impl: type[AssistantTypeT]

    # pylint: disable=too-many-arguments
    async def _create(
        self,
        model: str | BaseGPTModel,
        *,
        temperature: UndefinedOr[float] = UNDEFINED,
        max_tokens: UndefinedOr[int] = UNDEFINED,
        instruction: UndefinedOr[str] = UNDEFINED,
        max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        tools: UndefinedOr[Iterable[BaseTool]] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> AssistantTypeT:
        # pylint: disable=too-many-locals
        if is_defined(ttl_days) != is_defined(expiration_policy):
            raise ValueError("ttl_days and expiration policy must be both defined either undefined")

        expiration_config = ExpirationConfig.coerce(ttl_days=ttl_days, expiration_policy=expiration_policy)

        model_uri: str = ''
        if isinstance(model, str):
            model_uri = self._sdk.models.completions(model).uri
        elif isinstance(model, BaseGPTModel):
            model_uri = model.uri
            if not is_defined(temperature) and model.config.temperature is not None:
                temperature = model.config.temperature
            if not is_defined(max_tokens) and model.config.max_tokens is not None:
                max_tokens = model.config.max_tokens
        else:
            raise TypeError('model argument must be str, GPTModel object either undefined')

        tools_: tuple[BaseTool, ...] = ()
        if is_defined(tools):
            # NB: mypy doesn't love abstract class used as TypeVar substitution here
            tools_ = coerce_tuple(tools, BaseTool)  # type: ignore[type-abstract]

        request = CreateAssistantRequest(
            folder_id=self._folder_id,
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            labels=get_defined_value(labels, {}),
            expiration_config=expiration_config.to_proto(),
            instruction=get_defined_value(instruction, ''),
            prompt_truncation_options=get_prompt_trunctation_options(
                max_prompt_tokens=get_defined_value(max_prompt_tokens, None)
            ),
            model_uri=model_uri,
            completion_options=get_completion_options(
                temperature=temperature,
                max_tokens=max_tokens
            ),
            tools=[tool._to_proto() for tool in tools_]
        )

        async with self._client.get_service_stub(AssistantServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=ProtoAssistant,
            )

        return self._assistant_impl._from_proto(proto=response, sdk=self._sdk)

    async def _get(
        self,
        assistant_id: str,
        *,
        timeout: float = 60,
    ) -> AssistantTypeT:
        # TODO: we need a global per-sdk cache on ids to rule out
        # possibility we have two Assistants with same ids but different fields
        request = GetAssistantRequest(assistant_id=assistant_id)

        async with self._client.get_service_stub(AssistantServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoAssistant,
            )

        return self._assistant_impl._from_proto(proto=response, sdk=self._sdk)

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AssistantTypeT]:
        page_token_ = ''
        page_size_ = get_defined_value(page_size, 0)

        async with self._client.get_service_stub(AssistantServiceStub, timeout=timeout) as stub:
            while True:
                request = ListAssistantsRequest(
                    folder_id=self._folder_id,
                    page_size=page_size_,
                    page_token=page_token_,
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListAssistantsResponse,
                )
                for assistant_proto in response.assistants:
                    yield self._assistant_impl._from_proto(proto=assistant_proto, sdk=self._sdk)

                if not response.assistants:
                    return

                page_token_ = response.next_page_token


class AsyncAssistants(BaseAssistants[AsyncAssistant]):
    _assistant_impl = AsyncAssistant

    # pylint: disable=too-many-arguments
    async def create(
        self,
        model: str | BaseGPTModel,
        *,
        temperature: UndefinedOr[float] = UNDEFINED,
        max_tokens: UndefinedOr[int] = UNDEFINED,
        instruction: UndefinedOr[str] = UNDEFINED,
        max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        tools: UndefinedOr[Iterable[BaseTool]] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncAssistant:
        return await self._create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            instruction=instruction,
            max_prompt_tokens=max_prompt_tokens,
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            tools=tools,
            expiration_policy=expiration_policy,
            timeout=timeout,
        )

    async def get(
        self,
        assistant_id: str,
        *,
        timeout: float = 60,
    ) -> AsyncAssistant:
        return await self._get(
            assistant_id=assistant_id,
            timeout=timeout
        )

    async def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AsyncAssistant]:
        async for assistant in self._list(
            page_size=page_size,
            timeout=timeout
        ):
            yield assistant


class Assistants(BaseAssistants[Assistant]):
    _assistant_impl = Assistant

    __get = run_sync(BaseAssistants._get)
    __create = run_sync(BaseAssistants._create)
    __list = run_sync_generator(BaseAssistants._list)

    # pylint: disable=too-many-arguments
    def create(
        self,
        model: str | BaseGPTModel,
        *,
        temperature: UndefinedOr[float] = UNDEFINED,
        max_tokens: UndefinedOr[int] = UNDEFINED,
        instruction: UndefinedOr[str] = UNDEFINED,
        max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        tools: UndefinedOr[Iterable[BaseTool]] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> Assistant:
        return self.__create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            instruction=instruction,
            max_prompt_tokens=max_prompt_tokens,
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            tools=tools,
            expiration_policy=expiration_policy,
            timeout=timeout,
        )

    def get(
        self,
        assistant_id: str,
        *,
        timeout: float = 60,
    ) -> Assistant:
        return self.__get(
            assistant_id=assistant_id,
            timeout=timeout
        )

    def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[Assistant]:
        yield from self.__list(
            page_size=page_size,
            timeout=timeout
        )
