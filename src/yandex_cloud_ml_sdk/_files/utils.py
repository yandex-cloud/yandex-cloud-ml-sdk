from __future__ import annotations

from typing import Iterable, Union

from .file import BaseFile

FileType = Union[str, BaseFile, Iterable[BaseFile], Iterable[str]]


def coerce_file_ids(files: FileType) -> tuple[str, ...]:
    if isinstance(files, str):
        return (files, )

    if isinstance(files, BaseFile):
        return (files.id, )

    return tuple(
        file.id if isinstance(file, BaseFile) else file
        for file in files
    )
