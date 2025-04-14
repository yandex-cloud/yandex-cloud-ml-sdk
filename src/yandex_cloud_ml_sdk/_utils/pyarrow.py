from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

RecordType = dict[Any, Any]


async def read_dataset_records(path: str, batch_size: int | None) -> AsyncIterator[RecordType]:
    iterator = read_dataset_records_sync(path=path, batch_size=batch_size)

    def get_next() -> RecordType | None:
        try:
            return next(iterator)
        except StopIteration:
            return None

    while True:
        item = await asyncio.to_thread(get_next)
        if item is None:
            return

        yield item


def read_dataset_records_sync(path: str, batch_size: int | None) -> Iterator[RecordType]:
    import pyarrow.dataset as pd  # pylint: disable=import-outside-toplevel

    # we need use kwargs method to preserve original default value
    kwargs = {}
    if batch_size is not None:
        kwargs['batch_size'] = batch_size
    dataset = pd.dataset(source=path, format='parquet')
    for batch in dataset.to_batches(**kwargs):  # type: ignore[arg-type]
        yield from batch.to_pylist()
