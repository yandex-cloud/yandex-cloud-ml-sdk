from __future__ import annotations

import abc
import asyncio
import math
import pathlib
from typing import TYPE_CHECKING

import aiofiles

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.misc import PathLike, coerce_path, is_path_like

if TYPE_CHECKING:
    from .dataset import BaseDataset

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 500 * 1024 ** 2

MAX_CHUNK_SIZE = 5 * 1024 ** 3  # 5 GB
MAX_CHUNK_SIZE_PRETTY = '5GB'

MIN_CHUNK_SIZE = 5 * 1024 ** 2  # 5 MB
MIN_CHUNK_SIZE_PRETTY = '5MB'


class BaseUploader(abc.ABC):
    def __init__(self, chunk_size: int, parallelism: int):
        self._chunk_size = chunk_size
        self._parallelism = parallelism

    @abc.abstractmethod
    async def upload(self, path_or_iterator: PathLike, /, dataset: BaseDataset, timeout: float, upload_timeout: float) -> None:
        pass


def create_uploader(path_or_iterator: PathLike, chunk_size: int, parallelism: int | None) -> BaseUploader:
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
    async def upload(self, path: PathLike, /, dataset: BaseDataset, timeout: float, upload_timeout: float) -> None:
        path = coerce_path(path)
        size = path.stat().st_size

        # pylint: disable=protected-access
        presigned_url = await dataset._get_upload_url(size=size, timeout=timeout)
        logger.debug('Uploading data from %s to presigned url', path)
        async with aiofiles.open(path, mode='rb') as file_:
            data = await file_.read()

        # NB: here will be retries at sometime
        async with dataset._client.httpx() as client:
            response = await client.put(
                url=presigned_url,
                content=data,
                timeout=upload_timeout,
            )

        logger.debug("Data upload from %s to presigned url finished with a status %d", path, response.status_code)

        response.raise_for_status()


class MultipartUploader(BaseUploader):
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

            async with dataset._client.httpx() as client:
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
