# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import partial
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from typing_extensions import Self
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import ValidateDatasetRequest, ValidateDatasetResponse
from yandex.cloud.ai.dataset.v1.dataset_service_pb2_grpc import DatasetServiceStub
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.misc import PathLike, coerce_path
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation, OperationTypeT, ReturnsOperationMixin
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .dataset import AsyncDataset, Dataset, DatasetTypeT
from .uploaders import DEFAULT_CHUNK_SIZE, create_uploader
from .validation import DatasetValidationResult

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    from .domain import BaseDatasets


DEFAULT_OPERATION_POLL_TIMEOUT = 6 * 60 * 60  # 6 hours

logger = get_logger(__name__)


@dataclass
class BaseDatasetDraft(Generic[DatasetTypeT, OperationTypeT], ReturnsOperationMixin[OperationTypeT]):
    """
    A class for handling operations with the dataset in a draft state."""
    _domain: BaseDatasets
    _dataset_impl: type[DatasetTypeT] = field(init=False)
    #: the type of task associated with the dataset
    task_type: str | None = None
    #: the file path to the dataset
    path: PathLike | None = None
    #: the format in which the dataset will be uploaded
    upload_format: str | None = None
    #: the name of the dataset
    name: str | None = None
    #: a description of the dataset
    description: str | None = None
    #: metadata associated with the dataset
    metadata: str | None = None
    #: labels for categorizing the dataset
    labels: dict[str, str] | None = None
    #: a flag indicating if iy\t is allowed to use the dataset to improve the models quality. Default false.
    allow_data_logging: bool | None = None

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
        logger.debug('Starting dataset %s validation operation', dataset.id)
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

        logger.info('Dataset %s validation operation %s started', dataset.id, result.id)
        return self._operation_impl(
            id=result.id,
            sdk=self._sdk,
            result_type=self._dataset_impl,
            proto_result_type=ValidateDatasetResponse,
            service_name='ai-foundation-models',
            transformer=partial(
                self._transform_operation_result,
                raise_on_validation_failure=raise_on_validation_failure,
            ),
            custom_default_poll_timeout=DEFAULT_OPERATION_POLL_TIMEOUT,
        )

    async def _upload_deferred(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        parallelism: int | None = None,
    ) -> OperationTypeT:
        """
        Upload data to a dataset in a deferred manner.

        :param timeout: the time to wait for the dataset creation operation.
            Defaults to 60 seconds.
        :param upload_timeout: the time to wait for the upload operation.
            Defaults to 360 seconds.
        :param raise_on_validation_failure: a flag indicating whether to raise an error if validation fails after the upload.
            Default is True.
        :param chunk_size: the size of chunks to use when uploading data.
            Default is defined by DEFAULT_CHUNK_SIZE.
        :param parallelism: the level of parallelism for the upload.
            Default is None, which means no limit.
        """
        self.validate()
        assert self.task_type
        assert self.upload_format
        assert self.path

        uploader = create_uploader(
            path_or_iterator=self.path,
            chunk_size=chunk_size,
            parallelism=parallelism
        )

        dataset = await self._domain._create_impl(
            task_type=self.task_type,
            upload_format=self.upload_format,
            name=self.name,
            description=self.description,
            metadata=self.metadata,
            labels=self.labels,
            allow_data_logging=self.allow_data_logging,
            timeout=timeout,
        )

        logger.debug("Uploading data from path %s to dataset %s with %s uploader", self.path, dataset.id, uploader)
        try:
            await uploader.upload(
                self.path,
                dataset=dataset,
                timeout=timeout,
                upload_timeout=upload_timeout
            )
        except Exception:
            logger.warning("Deleting dataset %s because of incompleted uploading", dataset.id)
            # in case of HTTP error while uploading we want to remove dataset draft,
            # because user don't have any access to this draft
            await dataset._delete(timeout=timeout)
            raise

        logger.info("Data from path %s to dataset %s successfully uploaded", self.path, dataset.id)

        operation = await self._validate_deferred(
            dataset=dataset,
            timeout=timeout,
            raise_on_validation_failure=raise_on_validation_failure,
        )
        return operation

    async def _upload(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = DEFAULT_OPERATION_POLL_TIMEOUT,
        poll_interval: float = 60,
        **kwargs,
    ) -> DatasetTypeT:
        """
        Upload data and wait for the operation to complete.

        :param timeout: the time to wait for the upload operation.
            Defaults to 60 seconds.
        :param poll_timeout: the time to wait for polling the operation status.
            Default is defined by DEFAULT_OPERATION_POLL_TIMEOUT.
        :param poll_interval: the interval at which to poll for operation status
            Defaults to 60 seconds).
        :param kwargs: additional keyword arguments passed to ``_upload_deferred``.
        """
        operation = await self._upload_deferred(
            **kwargs,
            timeout=timeout,
        )
        # pylint: disable=protected-access
        result = await operation._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )
        return result

@doc_from(BaseDatasetDraft)
class AsyncDatasetDraft(BaseDatasetDraft[AsyncDataset, AsyncOperation[AsyncDataset]]):
    _dataset_impl = AsyncDataset
    _operation_impl = AsyncOperation[AsyncDataset]

    @doc_from(BaseDatasetDraft._upload_deferred)
    async def upload_deferred(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        parallelism: int | None = None,
    ) -> AsyncOperation[AsyncDataset]:
        return await self._upload_deferred(
            timeout=timeout,
            upload_timeout=upload_timeout,
            raise_on_validation_failure=raise_on_validation_failure,
            chunk_size=chunk_size,
            parallelism=parallelism,
        )

    @doc_from(BaseDatasetDraft._upload)
    async def upload(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
        poll_timeout: int = DEFAULT_OPERATION_POLL_TIMEOUT,
        poll_interval: float = 60,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        parallelism: int | None = None,
    ):
        return await self._upload(
            timeout=timeout,
            upload_timeout=upload_timeout,
            raise_on_validation_failure=raise_on_validation_failure,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
            chunk_size=chunk_size,
            parallelism=parallelism,
        )


@doc_from(BaseDatasetDraft)
class DatasetDraft(BaseDatasetDraft[Dataset, Operation[Dataset]]):
    _dataset_impl = Dataset
    _operation_impl = Operation[Dataset]
    __upload_deferred = run_sync(BaseDatasetDraft._upload_deferred)
    __upload = run_sync(BaseDatasetDraft._upload)

    @doc_from(BaseDatasetDraft._upload_deferred)
    def upload_deferred(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        parallelism: int | None = None,
    ) -> Operation[Dataset]:
        return self.__upload_deferred(
            timeout=timeout,
            upload_timeout=upload_timeout,
            raise_on_validation_failure=raise_on_validation_failure,
            chunk_size=chunk_size,
            parallelism=parallelism,
        )

    @doc_from(BaseDatasetDraft._upload)
    def upload(
        self,
        *,
        timeout: float = 60,
        upload_timeout: float = 360,
        raise_on_validation_failure: bool = True,
        poll_timeout: int = DEFAULT_OPERATION_POLL_TIMEOUT,
        poll_interval: float = 60,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        parallelism: int | None = None,
    ):
        return self.__upload(
            timeout=timeout,
            upload_timeout=upload_timeout,
            raise_on_validation_failure=raise_on_validation_failure,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
            chunk_size=chunk_size,
            parallelism=parallelism,
        )


DatasetDraftT = TypeVar('DatasetDraftT', bound=BaseDatasetDraft)
