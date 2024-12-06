from __future__ import annotations

from typing import TYPE_CHECKING

import aiofiles

from yandex_cloud_ml_sdk._client import httpx_client
from yandex_cloud_ml_sdk._types.misc import PathLike, coerce_path

if TYPE_CHECKING:
    from .dataset import BaseDataset


MAX_FILE_SIZE = 5 * 1024 ** 3  # 5 GB


class SingleUploader:
    def __init__(self, dataset: BaseDataset):
        self._dataset = dataset

    async def upload(self, path: PathLike, timeout: float, upload_timeout: float) -> None:
        path = coerce_path(path)
        size = path.stat().st_size

        if size > MAX_FILE_SIZE:
            raise RuntimeError(
                f'file {path} is too big; in this version of SDK it must be less '
                'than 5GB'
            )

        # pylint: disable=protected-access
        presigned_url = await self._dataset._get_upload_url(size=size, timeout=timeout)
        async with aiofiles.open(path, mode='rb') as file_:
            data = await file_.read()

        # NB: here will be retries at sometime
        async with httpx_client() as client:
            response = await client.put(
                url=presigned_url,
                content=data,
                timeout=upload_timeout,
            )

        response.raise_for_status()
