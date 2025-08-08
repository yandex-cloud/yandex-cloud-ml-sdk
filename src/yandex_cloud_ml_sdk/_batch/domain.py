# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterator

from yandex.cloud.ai.batch_inference.v1.batch_inference_service_pb2 import (
    ListBatchInferencesRequest, ListBatchInferencesResponse
)
from yandex.cloud.ai.batch_inference.v1.batch_inference_service_pb2_grpc import BatchInferenceServiceStub
from yandex.cloud.ai.batch_inference.v1.batch_inference_task_pb2 import BatchInferenceTask as ProtoBatchInferenceTask

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.batch.operation import (
    AsyncBatchTaskOperation, BatchTaskOperation, BatchTaskOperationTypeT
)
from yandex_cloud_ml_sdk._types.batch.status import BatchTaskStatus
from yandex_cloud_ml_sdk._types.batch.task_info import BatchTaskInfo
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.proto import ProtoEnumCoercible
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

logger = get_logger(__name__)


class BaseBatch(BaseDomain, Generic[BatchTaskOperationTypeT]):
    _operation_impl: type[BatchTaskOperationTypeT]

    async def _get(
        self,
        task: str | BatchTaskInfo,
        *,
        timeout: float = 60,
    ) -> BatchTaskOperationTypeT:
        logger.debug('Fetching batch task %s from server', task)

        if isinstance(task, BatchTaskInfo):
            return self._operation_impl(
                id=task.task_id,
                sdk=self._sdk
            )

        assert isinstance(task, str)

        task_obj = self._operation_impl(
            id=task,
            sdk=self._sdk,
        )
        task_info = await task_obj._get_task_info(timeout=timeout)

        logger.debug('Batch task %r fetched', task_info)

        return task_obj

    async def _list_operations(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        status: UndefinedOr[ProtoEnumCoercible[BatchTaskStatus]] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncIterator[BatchTaskOperationTypeT]:
        logger.debug('Fetching batch task list')

        async for task_proto in self._list_impl(
            page_size=page_size,
            status=status,
            timeout=timeout
        ):
            yield self._operation_impl(
                id=task_proto.task_id,
                sdk=self._sdk,
            )

    async def _list_info(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        status: UndefinedOr[ProtoEnumCoercible[BatchTaskStatus]] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncIterator[BatchTaskInfo]:
        logger.debug('Fetching batch task list')

        async for task_proto in self._list_impl(
            page_size=page_size,
            status=status,
            timeout=timeout
        ):
            yield BatchTaskInfo._from_proto(proto=task_proto, sdk=self._sdk)

    async def _list_impl(
        self,
        *,
        page_size: UndefinedOr[int],
        status: UndefinedOr[ProtoEnumCoercible[BatchTaskStatus]],
        timeout: float
    ) -> AsyncIterator[ProtoBatchInferenceTask]:
        logger.debug('Fetching batch task list')

        page_size_ = get_defined_value(page_size, 0)
        page_token = ''
        status_: ProtoEnumCoercible[BatchTaskStatus] = get_defined_value(status, 0)
        status_int = BatchTaskStatus._coerce(status_)

        async with self._client.get_service_stub(
            BatchInferenceServiceStub,
            timeout=timeout,
        ) as stub:
            while True:
                logger.debug(
                    'Fetching batch task list page of size %s with token %s',
                    page_size_, page_token,
                )

                request = ListBatchInferencesRequest(
                    folder_id=self._folder_id,
                    page_size=page_size_,
                    page_token=page_token,
                    status=status_int, # type: ignore[arg-type]
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListBatchInferencesResponse,
                )

                logger.debug(
                    '%d Batch tasks fetched for page with token %s',
                    len(response.tasks), page_token,
                )
                for task_proto in response.tasks:
                    yield task_proto

                if not response.tasks or not response.next_page_token:
                    return

                page_token = response.next_page_token


class AsyncBatch(BaseBatch[AsyncBatchTaskOperation]):
    _operation_impl = AsyncBatchTaskOperation

    async def get(
        self,
        task: str | BatchTaskInfo,
        *,
        timeout: float = 60,
    ) -> AsyncBatchTaskOperation:
        return await self._get(task=task, timeout=timeout)

    async def list_operations(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        status: UndefinedOr[ProtoEnumCoercible[BatchTaskStatus]] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AsyncBatchTaskOperation]:
        async for task in self._list_operations(
            page_size=page_size,
            status=status,
            timeout=timeout
        ):
            yield task

    async def list_info(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        status: UndefinedOr[ProtoEnumCoercible[BatchTaskStatus]] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[BatchTaskInfo]:
        async for task in self._list_info(
            page_size=page_size,
            status=status,
            timeout=timeout
        ):
            yield task


class Batch(BaseBatch[BatchTaskOperation]):
    _operation_impl = BatchTaskOperation
    __get = run_sync(BaseBatch._get)
    __list_operations = run_sync_generator(BaseBatch._list_operations)
    __list_info = run_sync_generator(BaseBatch._list_info)

    def get(
        self,
        task: str | BatchTaskInfo,
        *,
        timeout: float = 60,
    ) -> BatchTaskOperation:
        return self.__get(task=task, timeout=timeout)

    def list_operations(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        status: UndefinedOr[ProtoEnumCoercible[BatchTaskStatus]] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[BatchTaskOperation]:
        yield from self.__list_operations(
            page_size=page_size,
            status=status,
            timeout=timeout
        )

    def list_info(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        status: UndefinedOr[ProtoEnumCoercible[BatchTaskStatus]] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[BatchTaskInfo]:
        yield from self.__list_info(
            page_size=page_size,
            status=status,
            timeout=timeout
        )
