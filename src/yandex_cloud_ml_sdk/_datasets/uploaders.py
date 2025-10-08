from __future__ import annotations

import abc
import asyncio
import math
import pathlib
from typing import TYPE_CHECKING

import aiofiles

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.misc import PathLike, coerce_path, is_path_like
from yandex_cloud_ml_sdk._utils.doc import doc_from

if TYPE_CHECKING:
    from .dataset import BaseDataset

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 100 * 1024 ** 2  # 100 Mb

MAX_CHUNK_SIZE = 5 * 1024 ** 3  # 5 GB
MAX_CHUNK_SIZE_PRETTY = '5GB'

MIN_CHUNK_SIZE = 5 * 1024 ** 2  # 5 MB
MIN_CHUNK_SIZE_PRETTY = '5MB'


class BaseUploader(abc.ABC):
    """This class defines the interface for uploading datasets, allowing for
    different implementations based on the size of the dataset and the
    desired upload strategy.

    :param _chunk_size: the size of chunks to upload.
    :param _parallelism: the level of parallelism for uploads.
    """
    def __init__(self, chunk_size: int, parallelism: int):
        self._chunk_size = chunk_size
        self._parallelism = parallelism

    @abc.abstractmethod
    async def upload(self, path_or_iterator: PathLike, /, dataset: BaseDataset, timeout: float, upload_timeout: float) -> None:
        """Upload the dataset to a specified location.

        :param path_or_iterator: the path or iterator to the data to be uploaded.
        :param dataset: the dataset object containing metadata and methods for upload.
        :param timeout: the overall time to wait for the upload operation.
        :param upload_timeout: the time to wait for individual upload requests.
        """
        pass


def create_uploader(path_or_iterator: PathLike, chunk_size: int, parallelism: int | None) -> BaseUploader:
    """Create an appropriate uploader based on the provided parameters.

    :param path_or_iterator: the path or iterator to the data to be uploaded.
    :param chunk_size: the size of chunks to upload.
    :param parallelism: the level of parallelism for uploads.
    """
    if not is_path_like(path_or_iterator):
        raise NotImplementedError('only paths are supported yet')

    if chunk_size <= 0:
        chunk_size = DEFAULT_CHUNK_SIZE

    if MIN_CHUNK_SIZE > chunk_size or chunk_size > MAX_CHUNK_SIZE:
        raise ValueError(
            'chunk_size should be between '
            f'{MIN_CHUNK_SIZE} bytes ({MIN_CHUNK_SIZE_PRETTY}) and '
            f'{MAX_CHUNK_SIZE} bytes ({MAX_CHUNK_SIZE_PRETTY})'
        )

    path = coerce_path(path_or_iterator)
    size = path.stat().st_size

    kls: type[BaseUploader]
    if size <= chunk_size:
        kls = SingleUploader
    else:
        kls = MultipartUploader

    parallelism = parallelism or 1
    parallelism = max(parallelism, 1)

    return kls(chunk_size=chunk_size, parallelism=parallelism)


class SingleUploader(BaseUploader):
    """This class implements the upload method for datasets that can be uploaded in one go without needing to split into multiple parts."""

    async def upload(self, path: PathLike, /, dataset: BaseDataset, timeout: float, upload_timeout: float) -> None:
        """Upload the dataset using a single request or a multipart upload.

        :param path: the path to the data to be uploaded.
        :param dataset: the dataset object containing metadata and methods for upload.
        :param timeout: the overall time to wait for the upload operation.
        :param upload_timeout: the time to wait for the individual upload request.
        """
        path = coerce_path(path)
        size = path.stat().st_size

        # pylint: disable=protected-access
        presigned_url = await dataset._get_upload_url(size=size, timeout=timeout)
        logger.debug('Uploading data from %s to presigned url', path)
        async with aiofiles.open(path, mode='rb') as file_:
            data = await file_.read()

        # NB: here will be retries at sometime
        async with dataset._client.httpx(timeout=timeout, auth=False) as client:
            response = await client.put(
                url=presigned_url,
                content=data,
                timeout=upload_timeout,
            )

        logger.debug("Data upload from %s to presigned url finished with a status %d", path, response.status_code)

        response.raise_for_status()


class MultipartUploader(BaseUploader):
    """This class implements the upload method for datasets that need to
    be split into smaller parts (chunks) for upload. It allows for
    concurrent uploads of these chunks to improve performance.

    :param _semaphore: a semaphore to limit the number of concurrent uploads based on the specified parallelism.
    """

    def __init__(self, chunk_size: int, parallelism: int):
        super().__init__(chunk_size=chunk_size, parallelism=parallelism)
        self._semaphore = asyncio.Semaphore(parallelism)

    async def _upload_part(
        self,
        dataset: BaseDataset,
        path: pathlib.Path,
        chunk_number: int,
        chunk_size: int,
        url: str,
        timeout: float
    ) -> str:
        async with self._semaphore:
            logger.debug("Uploading %d chunk from %s to presigned url", chunk_number, path)
            async with aiofiles.open(path, 'rb') as f:
                await f.seek(chunk_number * chunk_size)
                data = await f.read(chunk_size)

            async with dataset._client.httpx(timeout=timeout, auth=False) as client:
                response = await client.put(
                    url=url,
                    content=data,
                    timeout=timeout,
                )

            del data

            if 'etag' not in response.headers:
                raise RuntimeError('missing etag header in s3 response')

            logger.debug(
                "%d chunk from %s upload to presigned url returned status code %d",
                chunk_number, path, response.status_code
            )

            return response.headers['etag']

    @doc_from(SingleUploader.upload)
    async def upload(self, path: PathLike, /, dataset: BaseDataset, timeout: float, upload_timeout: float) -> None:
        path = coerce_path(path)
        size = path.stat().st_size

        parts = math.floor(size / self._chunk_size)
        real_chunk_size = math.ceil(size / parts)

        # pylint: disable=protected-access
        urls = await dataset._start_multipart_upload(
            size_bytes=size,
            parts=parts,
            timeout=timeout,
        )

        upload_coros = []
        for i, url in enumerate(urls):
            upload_coro = self._upload_part(
                dataset,
                path,
                chunk_number=i,
                chunk_size=real_chunk_size,
                url=url,
                timeout=upload_timeout
            )
            upload_coros.append(upload_coro)

        etags = await asyncio.gather(*upload_coros)

        chunks_etags = [(i + 1, etag) for i, etag in enumerate(etags)]
        await dataset._finish_multipart_upload(chunks_etags, timeout=timeout)
