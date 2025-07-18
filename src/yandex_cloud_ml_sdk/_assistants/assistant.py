# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import dataclasses
from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Generic, Iterator, TypeVar

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.assistant_pb2 import Assistant as ProtoAssistant
from yandex.cloud.ai.assistants.v1.assistant_service_pb2 import (
    DeleteAssistantRequest, DeleteAssistantResponse, ListAssistantVersionsRequest, ListAssistantVersionsResponse,
    UpdateAssistantRequest
)
from yandex.cloud.ai.assistants.v1.assistant_service_pb2_grpc import AssistantServiceStub

from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel
from yandex_cloud_ml_sdk._runs.run import AsyncRun, Run, RunTypeT
from yandex_cloud_ml_sdk._threads.thread import AsyncThread, Thread, ThreadTypeT
from yandex_cloud_ml_sdk._tools.tool import BaseTool
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import ExpirableResource, safe_on_delete
from yandex_cloud_ml_sdk._types.schemas import ResponseType
from yandex_cloud_ml_sdk._utils.proto import proto_to_dict
from yandex_cloud_ml_sdk._utils.sync import run_sync_generator_impl, run_sync_impl

from .prompt_truncation_options import PromptTruncationOptions, PromptTruncationStrategyType

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class BaseAssistant(ExpirableResource, Generic[RunTypeT, ThreadTypeT]):
    expiration_config: ExpirationConfig
    model: BaseGPTModel
    instruction: str | None
    prompt_truncation_options: PromptTruncationOptions
    tools: tuple[BaseTool, ...]
    response_format: ResponseType | None

    @property
    def max_prompt_tokens(self) -> int | None:
        return self.prompt_truncation_options.max_prompt_tokens

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoAssistant, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)

        if proto.HasField('response_format'):
            response_format = proto.response_format
            if response_format.HasField("json_schema"):
                kwargs['response_format'] = {
                    'json_schema': proto_to_dict(response_format.json_schema.schema)
                }
            elif response_format.HasField('json_object'):
                if response_format.json_object:
                    kwargs['response_format'] = 'json'
            else:
                raise RuntimeError(f'Unknown {response_format=}, try to upgrade yandex-cloud-ml-sdk')

        model = sdk.models.completions(proto.model_uri)
        completion_options = proto.completion_options
        if completion_options.HasField('max_tokens'):
            model = model.configure(max_tokens=completion_options.max_tokens.value)
        if completion_options.HasField('temperature'):
            model = model.configure(temperature=completion_options.temperature.value)
        kwargs['model'] = model

        kwargs['tools'] = tuple(
            BaseTool._from_upper_proto(tool, sdk=sdk)
            for tool in proto.tools
        )
        kwargs['prompt_truncation_options'] = PromptTruncationOptions._from_proto(
            proto=proto.prompt_truncation_options,
            sdk=sdk
        )

        return kwargs

    # pylint: disable=too-many-arguments
    @safe_on_delete
    async def _update(
        self,
        *,
        model: UndefinedOr[str | BaseGPTModel] = UNDEFINED,
        temperature: UndefinedOr[float] = UNDEFINED,
        max_tokens: UndefinedOr[int] = UNDEFINED,
        instruction: UndefinedOr[str] = UNDEFINED,
        max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        tools: UndefinedOr[Iterable[BaseTool]] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        # pylint: disable=too-many-locals
        prompt_truncation_options = PromptTruncationOptions._coerce(
            max_prompt_tokens=max_prompt_tokens,
            strategy=prompt_truncation_strategy
        )

        request_kwargs = self._sdk.assistants._make_request_kwargs(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            instruction=instruction,
            max_prompt_tokens=max_prompt_tokens,
            prompt_truncation_strategy=prompt_truncation_strategy,
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            tools=tools,
            expiration_policy=expiration_policy,
            response_format=response_format
        )

        request = UpdateAssistantRequest(
            assistant_id=self.id,
            **request_kwargs,
        )
        model_uri = request_kwargs.get('model_uri', UNDEFINED)

        self._fill_update_mask(
            request.update_mask,
            {
                'name': name,
                'description': description,
                'labels': labels,
                'expiration_config.ttl_days': ttl_days,
                'expiration_config.expiration_policy': expiration_policy,
                'instruction': instruction,
                'model_uri': model_uri,
                'completion_options.temperature': temperature,
                'completion_options.max_tokens': max_tokens,
                'tools': tools,
                'response_format': response_format,
            } | prompt_truncation_options._get_update_paths()
        )

        async with self._client.get_service_stub(AssistantServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Update,
                request,
                timeout=timeout,
                expected_type=ProtoAssistant,
            )
        self._update_from_proto(response)

        return self

    @safe_on_delete
    async def _delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        request = DeleteAssistantRequest(assistant_id=self.id)

        async with self._client.get_service_stub(AssistantServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Delete,
                request,
                timeout=timeout,
                expected_type=DeleteAssistantResponse,
            )
            object.__setattr__(self, '_deleted', True)

    async def _list_versions(
        self,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AssistantVersion]:
        page_token_ = get_defined_value(page_token, '')
        page_size_ = get_defined_value(page_size, 0)

        async with self._client.get_service_stub(AssistantServiceStub, timeout=timeout) as stub:
            while True:
                request = ListAssistantVersionsRequest(
                    assistant_id=self.id,
                    page_size=page_size_,
                    page_token=page_token_,
                )

                response = await self._client.call_service(
                    stub.ListVersions,
                    request,
                    timeout=timeout,
                    expected_type=ListAssistantVersionsResponse,
                )
                for version in response.versions:
                    yield AssistantVersion(
                        id=version.id,
                        assistant=ReadOnlyAssistant._from_proto(
                            sdk=self._sdk,
                            proto=version.assistant
                        ),
                        update_mask=tuple(a for a in version.update_mask.paths)
                    )

                if not response.versions:
                    return

                page_token_ = response.next_page_token

    @safe_on_delete
    async def _run_impl(
        self,
        thread: str | ThreadTypeT,
        *,
        stream: bool,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        custom_prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        custom_response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> RunTypeT:
        return await self._sdk.runs._create(
            assistant=self,
            thread=thread,
            stream=stream,
            custom_temperature=custom_temperature,
            custom_max_tokens=custom_max_tokens,
            custom_max_prompt_tokens=custom_max_prompt_tokens,
            custom_prompt_truncation_strategy=custom_prompt_truncation_strategy,
            custom_response_format=custom_response_format,
            timeout=timeout,
        )

    async def _run(
        self,
        thread: str | ThreadTypeT,
        *,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        custom_prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        custom_response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> RunTypeT:
        return await self._run_impl(
            thread=thread,
            stream=False,
            custom_temperature=custom_temperature,
            custom_max_tokens=custom_max_tokens,
            custom_max_prompt_tokens=custom_max_prompt_tokens,
            custom_prompt_truncation_strategy=custom_prompt_truncation_strategy,
            custom_response_format=custom_response_format,
            timeout=timeout,
        )

    async def _run_stream(
        self,
        thread: str | ThreadTypeT,
        *,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        custom_prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        custom_response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> RunTypeT:
        return await self._run_impl(
            thread=thread,
            stream=True,
            custom_temperature=custom_temperature,
            custom_max_tokens=custom_max_tokens,
            custom_max_prompt_tokens=custom_max_prompt_tokens,
            custom_prompt_truncation_strategy=custom_prompt_truncation_strategy,
            custom_response_format=custom_response_format,
            timeout=timeout,
        )



@dataclasses.dataclass(frozen=True)
class ReadOnlyAssistant(BaseAssistant[RunTypeT, ThreadTypeT]):
    name: str | None
    description: str | None
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    expires_at: datetime
    labels: dict[str, str] | None


@dataclasses.dataclass(frozen=True)
class AssistantVersion:
    id: str
    assistant: ReadOnlyAssistant
    update_mask: tuple[str, ...]


class AsyncAssistant(ReadOnlyAssistant[AsyncRun, AsyncThread]):
    async def update(
        self,
        *,
        model: UndefinedOr[str | BaseGPTModel] = UNDEFINED,
        temperature: UndefinedOr[float] = UNDEFINED,
        max_tokens: UndefinedOr[int] = UNDEFINED,
        instruction: UndefinedOr[str] = UNDEFINED,
        max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        tools: UndefinedOr[Iterable[BaseTool]] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        return await self._update(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            instruction=instruction,
            max_prompt_tokens=max_prompt_tokens,
            prompt_truncation_strategy=prompt_truncation_strategy,
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            tools=tools,
            expiration_policy=expiration_policy,
            response_format=response_format,
            timeout=timeout
        )

    async def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        await self._delete(timeout=timeout)

    async def list_versions(
        self,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AssistantVersion]:
        async for version in self._list_versions(
            page_size=page_size,
            page_token=page_token,
            timeout=timeout,
        ):
            yield version

    async def run(
        self,
        thread: str | AsyncThread,
        *,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        custom_prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        custom_response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncRun:
        return await self._run(
            thread=thread,
            custom_temperature=custom_temperature,
            custom_max_tokens=custom_max_tokens,
            custom_max_prompt_tokens=custom_max_prompt_tokens,
            custom_prompt_truncation_strategy=custom_prompt_truncation_strategy,
            custom_response_format=custom_response_format,
            timeout=timeout
        )

    async def run_stream(
        self,
        thread: str | AsyncThread,
        *,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        custom_prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        custom_response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncRun:
        return await self._run_stream(
            thread=thread,
            custom_temperature=custom_temperature,
            custom_max_tokens=custom_max_tokens,
            custom_max_prompt_tokens=custom_max_prompt_tokens,
            custom_prompt_truncation_strategy=custom_prompt_truncation_strategy,
            custom_response_format=custom_response_format,
            timeout=timeout
        )


class Assistant(ReadOnlyAssistant[Run, Thread]):
    def update(
        self,
        *,
        model: UndefinedOr[str | BaseGPTModel] = UNDEFINED,
        temperature: UndefinedOr[float] = UNDEFINED,
        max_tokens: UndefinedOr[int] = UNDEFINED,
        instruction: UndefinedOr[str] = UNDEFINED,
        max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        tools: UndefinedOr[Iterable[BaseTool]] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        return run_sync_impl(self._update(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            instruction=instruction,
            max_prompt_tokens=max_prompt_tokens,
            prompt_truncation_strategy=prompt_truncation_strategy,
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            tools=tools,
            expiration_policy=expiration_policy,
            response_format=response_format,
            timeout=timeout
        ), self._sdk)

    def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        run_sync_impl(self._delete(timeout=timeout), self._sdk)

    def list_versions(
        self,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[AssistantVersion]:
        yield from run_sync_generator_impl(
            self._list_versions(
                page_size=page_size,
                page_token=page_token,
                timeout=timeout,
            ),
            self._sdk
        )

    def run(
        self,
        thread: str | Thread,
        *,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        custom_prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        custom_response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> Run:
        return run_sync_impl(self._run(
            thread=thread,
            custom_temperature=custom_temperature,
            custom_max_tokens=custom_max_tokens,
            custom_max_prompt_tokens=custom_max_prompt_tokens,
            custom_prompt_truncation_strategy=custom_prompt_truncation_strategy,
            custom_response_format=custom_response_format,
            timeout=timeout
        ), self._sdk)

    def run_stream(
        self,
        thread: str | Thread,
        *,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        custom_prompt_truncation_strategy: UndefinedOr[PromptTruncationStrategyType] = UNDEFINED,
        custom_response_format: UndefinedOr[ResponseType] = UNDEFINED,
        timeout: float = 60,
    ) -> Run:
        return run_sync_impl(self._run_stream(
            thread=thread,
            custom_temperature=custom_temperature,
            custom_max_tokens=custom_max_tokens,
            custom_max_prompt_tokens=custom_max_prompt_tokens,
            custom_prompt_truncation_strategy=custom_prompt_truncation_strategy,
            custom_response_format=custom_response_format,
            timeout=timeout
        ), self._sdk)


AssistantTypeT = TypeVar('AssistantTypeT', bound=BaseAssistant)
