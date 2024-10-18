# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.assistant_pb2 import Assistant as ProtoAssistant
from yandex.cloud.ai.assistants.v1.assistant_service_pb2 import (
    DeleteAssistantRequest, DeleteAssistantResponse, ListAssistantVersionsRequest, ListAssistantVersionsResponse,
    UpdateAssistantRequest
)
from yandex.cloud.ai.assistants.v1.assistant_service_pb2_grpc import AssistantServiceStub

from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._types.resource import BaseDeleteableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .utils import get_completion_options, get_prompt_trunctation_options

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class BaseAssistant(BaseDeleteableResource):
    expiration_config: ExpirationConfig
    model: BaseGPTModel
    instruction: str | None
    max_prompt_tokens: int | None

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoAssistant, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)

        model = sdk.models.completions(proto.model_uri)
        if max_tokens := proto.completion_options.max_tokens.value:
            model = model.configure(max_tokens=max_tokens)
        if temperature := proto.completion_options.temperature.value:
            model = model.configure(temperature=temperature)
        kwargs['model'] = model

        if max_prompt_tokens := proto.prompt_truncation_options.max_prompt_tokens.value:
            kwargs['max_prompt_tokens'] = max_prompt_tokens

        kwargs['expiration_config'] = ExpirationConfig.coerce(
            ttl_days=proto.expiration_config.ttl_days,
            expiration_policy=proto.expiration_config.expiration_policy,  # type: ignore[arg-type]
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
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        # pylint: disable=too-many-locals
        expiration_config = ExpirationConfig.coerce(
            ttl_days=ttl_days,
            expiration_policy=expiration_policy
        )

        model_uri: str | None = None
        model_temperature: float | None = self.model.config.temperature
        model_max_tokens: int | None = self.model.config.max_tokens

        if is_defined(model):
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

        request = UpdateAssistantRequest(
            assistant_id=self.id,
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            labels=get_defined_value(labels, {}),
            instruction=get_defined_value(instruction, ''),
            expiration_config=expiration_config.to_proto(),
            prompt_truncation_options=get_prompt_trunctation_options(
                max_prompt_tokens=get_defined_value(max_prompt_tokens, None)
            ),
            completion_options=get_completion_options(
                temperature=model_temperature,
                max_tokens=model_max_tokens
            )
        )
        if model_uri:
            request.model_uri = model_uri

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
                'completion_options.temperature': model_temperature,
                'completion_options.max_tokens': model_max_tokens,
                'prompt_truncation_options.max_prompt_tokens': max_prompt_tokens,
            }
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


@dataclasses.dataclass(frozen=True)
class ReadOnlyAssistant(BaseAssistant):
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


class AsyncAssistant(ReadOnlyAssistant):
    update = ReadOnlyAssistant._update
    delete = ReadOnlyAssistant._delete
    list_versions = ReadOnlyAssistant._list_versions


class Assistant(ReadOnlyAssistant):
    update = run_sync(ReadOnlyAssistant._update)
    delete = run_sync(ReadOnlyAssistant._delete)
    list_versions = run_sync_generator(ReadOnlyAssistant._list_versions)
