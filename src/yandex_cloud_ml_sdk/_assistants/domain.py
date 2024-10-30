# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterable

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
        model_temperature: float | None = None
        model_max_tokens: int | None = None
        if isinstance(model, str):
            model_uri = self._sdk.models.completions(model).uri
        elif isinstance(model, BaseGPTModel):
            model_uri = model.uri
            model_temperature = model.config.temperature
            model_max_tokens = model.config.max_tokens
        else:
            raise TypeError('model argument must be str, GPTModel object either undefined')

        model_temperature = get_defined_value(temperature, model_temperature)
        model_max_tokens = get_defined_value(max_tokens, model_max_tokens)

        tools_: tuple[BaseTool, ...] = ()
        if is_defined(tools):
            tools_ = coerce_tuple(tools, BaseTool)

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
                temperature=model_temperature,
                max_tokens=model_max_tokens
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
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AssistantTypeT]:
        page_token_ = get_defined_value(page_token, '')
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

    get = BaseAssistants._get
    create = BaseAssistants._create
    list = BaseAssistants._list


class Assistants(BaseAssistants[Assistant]):
    _assistant_impl = Assistant

    get = run_sync(BaseAssistants._get)
    create = run_sync(BaseAssistants._create)
    list = run_sync_generator(BaseAssistants._list)
