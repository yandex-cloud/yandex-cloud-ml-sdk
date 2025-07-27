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
    """
    Base class for implementing AI Assistants in Yandex Cloud ML SDK.

    This class provides core functionality for AI Assistants including:
    - Configuration management (expiration, model, instructions)
    - Thread and run management
    - Tool integration
    - Prompt processing

    The class follows the Template Method pattern, allowing subclasses to override
    specific behaviors while maintaining the overall workflow. It's designed to be
    thread-safe for concurrent usage.

    Example:

    .. code-block:: python
        class MyAssistant(BaseAssistant):
            def process_run(self, run: RunTypeT) -> Any:
                # Custom run processing logic

        assistant = MyAssistant(
            model=GPTModel.YANDEX_GPT,
            instruction="You are a helpful assistant",
            tools=[SearchTool(), CalculatorTool()]
        )

    :param expiration_config: Expiration configuration for the assistant. Determines when the assistant should be considered expired.
        Read more about possible ExpirationConfig format in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/create#yandex.cloud.ai.common.ExpirationConfig>`_.
    :type expiration_config: ExpirationConfig
    :param model: The GPT model used by the assistant. Defines the underlying AI model capabilities.
        Read more about possible GPT models in the `documentation <https://yandex.cloud/ru/docs/foundation-models/concepts/yandexgpt/models>`_.
    :type model: BaseGPTModel
    :param instruction: Instructions or guidelines that the assistant should follow. These instructions guide the assistant's behavior and responses.
    :type instruction: str or None
    :param prompt_truncation_options: Options for truncating thread messages.Controls how messages are truncated when forming the prompt.
        Read more about possible PromptTruncationOptions format in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/Assistant/create#yandex.cloud.ai.assistants.v1.PromptTruncationOptions>`_.
    :type prompt_truncation_options: PromptTruncationOptions
    :param tools: Tools available to the assistant. Can be a sequence or a single tool. Tools must implement BaseTool interface.
        Read more about available tools for assistant in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/create#yandex.cloud.ai.assistants.v1.Tool>`_.
    :type tools: tuple[BaseTool, ...]
    :param response_format: A format of the response returned by the assistant. Could be a JsonSchema, a JSON string, a pydantic model or None.
        Read more about response_format for assistant in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/create#yandex.cloud.ai.assistants.v1.ResponseFormat2>`_.
    :type response_format: ResponseType or None
    """
    expiration_config: ExpirationConfig
    model: BaseGPTModel
    instruction: str | None
    prompt_truncation_options: PromptTruncationOptions
    tools: tuple[BaseTool, ...]
    response_format: ResponseType | None

    @property
    def max_prompt_tokens(self) -> int | None:
        """
        Returns the maximum number of prompt tokens allowed for the assistant.

        :return: Maximum prompt tokens or None if not set.
        :rtype: int or None
        """
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
    """
    Read-only representation of an AI Assistant, including metadata such as name, description, and timestamps.
        Read more about some assistant parameters in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/get#yandex.cloud.ai.assistants.v1.Assistant>`_.

    :param name: Name of the assistant.
    :type name: str or None
    :param description: Description of the assistant.
    :type description: str or None
    :param created_by: Identifier of the creator.
    :type created_by: str
    :param created_at: Creation timestamp.
    :type created_at: datetime
    :param updated_by: Identifier of the last updater.
    :type updated_by: str
    :param updated_at: Last update timestamp.
    :type updated_at: datetime
    :param expires_at: Expiration timestamp.
    :type expires_at: datetime
    :param labels: Set of key-value pairs that can be used to organize and categorize the assistant.
    :type labels: dict[str, str] or None
    """
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
    """
    Represents a specific version of an Assistant.
        Read more about:
        - How to get list of versions of an assistant in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/listVersions>`_.
        - Parameters in version of an assistant in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/listVersions#yandex.cloud.ai.assistants.v1.AssistantVersion>`_.

    :param id: ID of the assistant version.
    :type id: str
    :param assistant: The assistant instance for this version.
    :type assistant: ReadOnlyAssistant
    :param update_mask: Mask specifying which fields were updated in this version. Mask also have a custom JSON encoding
    :type update_mask: tuple[str, ...]
    """
    id: str
    assistant: ReadOnlyAssistant
    update_mask: tuple[str, ...]


class AsyncAssistant(ReadOnlyAssistant[AsyncRun, AsyncThread]):
    """
    Provides asynchronous interface for managing and interacting with AI Assistants.

    This class implements a interactions with Yandex Cloud ML Assistant API with asynchronous interface.
    It's thread-safe and designed for high-performance concurrent usage.

    Example usage:

    .. code-block:: python
        async with AssistantClient() as client:
          assistant = await client.create(
             name="My Assistant",
             instructions="Help with coding tasks"
          )
          response = await assistant.run("How to write Python decorator?")
    """
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
        """
        Update the assistant's configuration asynchronously.
            Read more about some parameters in update function in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/update>`_.

        :param model: New model or model URI.
        :param temperature: A sampling temperature to use - higher values mean more random results. Should be a double number between 0 (inclusive) and 1 (inclusive).
        :param max_tokens: Maximum tokens for completion.
        :param instruction: New instruction for the assistant.
        :param max_prompt_tokens: Maximum prompt tokens.
        :param prompt_truncation_strategy: Strategy for prompt truncation.
        :param name: New name for the assistant.
        :param description: New description.
        :param labels: New labels.
        :param ttl_days: Time-to-live in days.
        :param tools: Iterable set of tools.
        :param expiration_policy: Expiration policy.
        :param response_format: A format of the response returned by the assistant as JSON.
        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        :return: Updated assistant instance.
        :rtype: Self
        """
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
        """
        Delete the assistant asynchronously.
            
        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        :type timeout: float
        :return: None
        """
        await self._delete(timeout=timeout)

    async def list_versions(
        self,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AssistantVersion]:
        """
        List all versions of the assistant asynchronously with pagination support.
        Versions are returned in reverse chronological order (newest first).

        The method implements automatic pagination - when page_token is not specified,
        it will automatically handle pagination until all versions are retrieved.
        If page_token is provided, returns only one page of results.
        
        Example usage:

        .. code-block:: python

            async for version in assistant.list_versions():
                print(version.id)

        :param page_size: Number of versions per page.
            Defaults to server-side setting (typically 50) if not specified (UNDEFINED).
        :param page_token: Token for the next page.
            Defaults to None (UNDEFINED) to start from the beginning and automatically paginate through all results.
        :param timeout: Timeout in seconds for each request.
            Defaults to 60 seconds.
        :return: Asynchronous iterator of AssistantVersion objects.
        :rtype: AsyncIterator[AssistantVersion]
        :raises:
            - TimeoutError: If the request times out
            - RuntimeError: If there are issues with the request
        :note: If no versions exist, the iterator will complete without yielding any items.
            Read more in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/listVersions>`_.
        """
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
        """
        Run the assistant asynchronously on a given thread.

        :param thread: Thread ID or AsyncThread instance.
            Read more about Thread in the `documentation <https://yandex.cloud/ru/docs/foundation-models/threads/api-ref/grpc/Thread/>`_.
        :param custom_temperature: A custom temperature for this run, should be a double number between 0 (inclusive) and 1 (inclusive).
        :param custom_max_tokens: Custom max tokens for this run.
        :param custom_max_prompt_tokens: Custom max prompt tokens for this run.
        :param custom_prompt_truncation_strategy: Custom prompt truncation strategy.
            Specifies the truncation strategy to use when the prompt exceeds the token limit.
            Read more about truncating thread messages in the `documentation <https://yandex.cloud/ru/docs/foundation-models/runs/api-ref/grpc/Run/create#yandex.cloud.ai.assistants.v1.PromptTruncationOptions2>`_.
        :param custom_response_format: A custom format of the response returned by the assistant as JSON object.
        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        :return: AsyncRun instance representing the run.
        :rtype: AsyncRun
        """
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
        """
        Run the assistant asynchronously on a given thread with streaming enabled. For example, it can be used to submit function call results when the run is waiting for user input.

        :param thread: Thread ID or AsyncThread instance.
        :param custom_temperature: A custom temperature for this run, should be a double number between 0 (inclusive) and 1 (inclusive).
        :param custom_max_tokens: Custom max tokens for this run.
        :param custom_max_prompt_tokens: Custom max prompt tokens for this run.
        :param custom_prompt_truncation_strategy: Custom prompt truncation strategy.
        :param custom_response_format: A custom format of the response returned by the assistant as JSON object.
        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        :return: AsyncRun instance representing the run.
        :rtype: AsyncRun
        """
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
    """
    Synchronous interface for managing and interacting with an AI Assistant.
    """
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
        """
        Update the assistant's configuration synchronously.

        :param model: New model or model URI.
        :param temperature: A sampling temperature to use - higher values mean more random results. Should be a double number between 0 (inclusive) and 1 (inclusive).
        :param max_tokens: Maximum tokens for completion.
        :param instruction: New instruction for the assistant.
        :param max_prompt_tokens: Maximum prompt tokens.
        :param prompt_truncation_strategy: Strategy for prompt truncation.
        :param name: New name for the assistant.
        :param description: New description.
        :param labels: New labels.
        :param ttl_days: Time-to-live in days.
        :param tools: Iterable of tools.
        :param expiration_policy: Expiration policy.
        :param response_format: A format of the response returned by the assistant as JSON.
        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        :return: Updated assistant instance.
        :rtype: Self
        """
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
        """
        Delete the assistant synchronously.

        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        """
        run_sync_impl(self._delete(timeout=timeout), self._sdk)

    def list_versions(
        self,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[AssistantVersion]:
        """
        List all versions of the assistant synchronously with pagination support.
        Versions are returned in reverse chronological order (newest first).

        The method implements automatic pagination - when page_token is not specified,
        it will automatically handle pagination until all versions are retrieved.
        If page_token is provided, returns only one page of results.
        
        Example usage:

        .. code-block:: python
            for version in assistant.list_versions():
                print(version.id)

        :param page_size: Number of versions per page.
            Defaults to server-side setting (typically 50) if not specified (UNDEFINED).
        :param page_token: Token for the next page.
            Defaults to None (UNDEFINED) to start from the beginning and automatically paginate through all results.
        :param timeout: Timeout in seconds for each request.
            Defaults to 60 seconds.
        :return: Iterator of AssistantVersion objects.
        :rtype: Iterator[AssistantVersion]
        :raises:
            - TimeoutError: If the request times out
            - RuntimeError: If there are issues with the request
        :note: If no versions exist, the iterator will complete without yielding any items.
            Read more in the `documentation <https://yandex.cloud/ru/docs/foundation-models/assistants/api-ref/grpc/Assistant/listVersions>`_.
        """
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
        """
        Run the assistant synchronously on a given thread.

        :param thread: Thread ID or Thread instance.
            Read more about Thread in the `documentation <https://yandex.cloud/ru/docs/foundation-models/threads/api-ref/grpc/Thread/>`_.
        :param custom_temperature: A custom temperature for this run, should be a double number between 0 (inclusive) and 1 (inclusive).
        :param custom_max_tokens: Custom max tokens for this run.
        :param custom_max_prompt_tokens: Custom max prompt tokens for this run.
        :param custom_prompt_truncation_strategy: Custom prompt truncation strategy.
        :param custom_response_format: A custom format of the response returned by the assistant as JSON object.
        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        :return: Run instance representing the run.
        :rtype: Run
        """
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
        """
        Run the assistant synchronously on a given thread with streaming enabled.

        :param thread: Thread ID or Thread instance.
            Read more about Thread in the `documentation <https://yandex.cloud/ru/docs/foundation-models/threads/api-ref/grpc/>`_.
        :param custom_temperature: A custom temperature for this run, should be a double number between 0 (inclusive) and 1 (inclusive).
        :param custom_max_tokens: Custom max tokens for this run.
        :param custom_max_prompt_tokens: Custom max prompt tokens for this run.
        :param custom_prompt_truncation_strategy: Custom prompt truncation strategy.
        :param custom_response_format: A custom format of the response returned by the assistant as JSON object.
        :param timeout: Timeout in seconds.
            Defaults to 60 seconds.
        :return: Run instance representing the run.
        :rtype: Run
        """
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
