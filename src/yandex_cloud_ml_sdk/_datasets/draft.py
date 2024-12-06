# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import partial
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from typing_extensions import Self
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import ValidateDatasetRequest, ValidateDatasetResponse
from yandex.cloud.ai.dataset.v1.dataset_service_pb2_grpc import DatasetServiceStub
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._types.misc import PathLike, coerce_path
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation, OperationTypeT, ReturnsOperationMixin
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .dataset import AsyncDataset, Dataset, DatasetTypeT
from .uploaders import SingleUploader
from .validation import DatasetValidationResult

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    from .domain import BaseDatasets


@dataclass
class BaseDatasetDraft(Generic[DatasetTypeT, OperationTypeT], ReturnsOperationMixin[OperationTypeT]):
    _domain: BaseDatasets
    _dataset_impl: type[DatasetTypeT] = field(init=False)

    task_type: str | None = None
    path: PathLike | None = None
    upload_format: str | None = None
    name: str | None = None
    description: str | None = None
    metadata: str | None = None
    labels: dict[str, str] | None = None

    @property
    def _sdk(self) -> BaseSDK:
        return self._domain._sdk

    def configure(self, **kwargs: Any) -> Self:
        return replace(self, **kwargs)

    def validate(self) -> None:
        if self.task_type is None:
            raise TypeError('task_type should be not None to upload a dataset')

        # NB: in future it must be xor with a stream attr
        if self.path is None:
            raise TypeError('path should be not None to upload a dataset')

        if self.path is not None:
            path = coerce_path(self.path)
            if not path.exists() or not path.is_file():
                raise TypeError('path should exists and be a file')

        if self.upload_format is None:
            raise TypeError('upload_format should be not None to upload a dataset')

    async def _transform_operation_result(
        self,
        proto: Any,
        timeout: float,
        raise_on_validation_failure: bool,
    ) -> DatasetTypeT:
        proto = cast(ValidateDatasetResponse, proto)
        validation_result = DatasetValidationResult._from_proto(proto=proto, sdk=self._sdk)
        if raise_on_validation_failure:
            validation_result.raise_for_status()

        return await self._domain._get(
            dataset_id=validation_result.dataset_id,
            timeout=timeout
        )

    async def _validate_deferred(
        self,
        *,
        dataset: DatasetTypeT,
        timeout: float,
        raise_on_validation_failure: bool,
    ) -> OperationTypeT:
        # validate_deferred should be a BaseDataset method by all means,
        # but I don't want to make Dataset operation-depentant generic,
        # because it is already too complicated.
        # And it is possible due to validate_deferred is not a part of SDK public API.
        request = ValidateDatasetRequest(
            dataset_id=dataset.id,
        )
        async with self._sdk._client.get_service_stub(
            DatasetServiceStub, timeout=timeout
        ) as stub:
            result = await self._sdk._client.call_service(
                stub.Validate,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )

        return self._operation_impl(
            id=result.id,
            sdk=self._sdk,
            result_type=self._dataset_impl,
            proto_result_type=ValidateDatasetResponse,
            service_name='ai-foundation-models',
            transformer=partial(
                self._transform_operation_result,
                raise_on_validation_failure=raise_on_validation_failure,
            )
        )

    async def _upload(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
    ) -> OperationTypeT:
        self.validate()
        assert self.task_type
        assert self.upload_format
        assert self.path

        dataset = await self._domain._create_impl(
            task_type=self.task_type,
            upload_format=self.upload_format,
            name=self.name,
            description=self.description,
            metadata=self.metadata,
            labels=self.labels,
            timeout=timeout,
        )

        try:
            uploader = SingleUploader(dataset)
            await uploader.upload(self.path, timeout=timeout, upload_timeout=upload_timeout)
        except Exception:
            # in case of HTTP error while uploading we want to remove dataset draft,
            # because user don't have any access to this draft
            await dataset._delete(timeout=timeout)
            raise

        operation = await self._validate_deferred(
            dataset=dataset,
            timeout=timeout,
            raise_on_validation_failure=raise_on_validation_failure,
        )
        return operation


class AsyncDatasetDraft(BaseDatasetDraft[AsyncDataset, AsyncOperation[AsyncDataset]]):
    _dataset_impl = AsyncDataset
    _operation_impl = AsyncOperation[AsyncDataset]

    async def upload(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
    ) -> AsyncOperation[AsyncDataset]:
        return await self._upload(
            timeout=timeout,
            upload_timeout=upload_timeout,
            raise_on_validation_failure=raise_on_validation_failure,
        )


class DatasetDraft(BaseDatasetDraft[Dataset, Operation[Dataset]]):
    _dataset_impl = Dataset
    _operation_impl = Operation[Dataset]
    __upload = run_sync(BaseDatasetDraft._upload)

    def upload(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
    ) -> Operation[Dataset]:
        return self.__upload(
            timeout=timeout,
            upload_timeout=upload_timeout,
            raise_on_validation_failure=raise_on_validation_failure,
        )


DatasetDraftT = TypeVar('DatasetDraftT', bound=BaseDatasetDraft)
