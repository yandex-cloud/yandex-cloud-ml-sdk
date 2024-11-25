from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dataset import BaseDataset


class Writer:
    def __init__(self, dataset: BaseDataset):
        self._dataset = dataset

    def _upload_single(self, data: bytes, url: str) -> None:
        pass

    def _upload_part(self, data: bytes, url: str) -> str:
        pass

    def _upload_multipart(self, data: bytes, presigned_urls: Iterable[str]) -> None:
        pass
