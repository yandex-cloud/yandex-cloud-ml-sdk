# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from dataclasses import astuple
from typing import Sequence

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_pb2 import (
    ClassificationSample as TextClassificationSampleProto
)
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_service_pb2 import (
    FewShotTextClassificationRequest, FewShotTextClassificationResponse, TextClassificationRequest,
    TextClassificationResponse
)
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_service_pb2_grpc import (
    TextClassificationServiceStub
)

from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelSyncMixin
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import TextClassifiersModelConfig
from .result import FewShotTextClassifiersModelResult, TextClassifiersModelResult, TextClassifiersModelResultBase
from .types import TextClassificationSample


class BaseTextClassifiersModel(
    ModelSyncMixin[TextClassifiersModelConfig, TextClassifiersModelResultBase]
):
    _config_type = TextClassifiersModelConfig
    _result_type = TextClassifiersModelResultBase

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
        *,
        task_description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[Sequence[str]] = UNDEFINED,
        samples: UndefinedOr[Sequence[TextClassificationSample]] = UNDEFINED,
    ) -> Self:
        return super().configure(
            task_description=task_description,
            labels=labels,
            samples=samples,
        )

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResultBase:
        if any(v is not None for v in astuple(self._config)):
            return await self._run_few_shot(text, timeout=timeout)

        return await self._run_classify(text, timeout=timeout)

    async def _run_classify(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResult:
        request = TextClassificationRequest(
            model_uri=self._uri,
            text=text,
        )
        async with self._client.get_service_stub(TextClassificationServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Classify,
                request,
                timeout=timeout,
                expected_type=TextClassificationResponse,
            )
            return TextClassifiersModelResult._from_proto(response, sdk=self._sdk)

    async def _run_few_shot(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> FewShotTextClassifiersModelResult:
        config = self._config

        if config.labels is None or config.task_description is None:
            raise ValueError(
                "Incorrect combination of config values. Use one of the three following combinations:\n",
                " * The `labels`, `task_description` and `samples` parameters must have specific values.\n"
                " * The `labels` and `task_description` parameters must"
                " have specific values while `samples` has the None value.\n"
                " * All three parameters — `labels', `task_description` and `samples` —"
                " must take the None value simultaneously."
            )

        samples = config.samples or []
        proto_samples = [
            TextClassificationSampleProto(
                text=sample['text'],
                label=sample['label'],
            ) for sample in samples
        ]
        request = FewShotTextClassificationRequest(
            model_uri=self._uri,
            text=text,
            task_description=config.task_description,
            labels=list(config.labels),
            samples=(proto_samples if proto_samples else None),
        )

        async with self._client.get_service_stub(TextClassificationServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.FewShotClassify,
                request,
                timeout=timeout,
                expected_type=FewShotTextClassificationResponse,
            )
            return FewShotTextClassifiersModelResult._from_proto(response, sdk=self._sdk)


class AsyncTextClassifiersModel(BaseTextClassifiersModel):
    async def run(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResultBase:
        return await self._run(
            text=text,
            timeout=timeout
        )


class TextClassifiersModel(BaseTextClassifiersModel):
    __run = run_sync(BaseTextClassifiersModel._run)

    def run(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResultBase:
        return self.__run(
            text=text,
            timeout=timeout
        )
