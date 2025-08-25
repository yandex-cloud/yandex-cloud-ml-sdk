from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

RecordType = dict[Any, Any]
#: Type alias for a dataset record represented as a dictionary with any keys and values.


async def read_dataset_records(path: str, batch_size: int | None) -> AsyncIterator[RecordType]:
    """
    Asynchronously read dataset records from a Parquet file.
    
    This function provides an asynchronous interface for reading records from
    a Parquet dataset file. It internally uses the synchronous version and
    executes it in a thread to avoid blocking the event loop.
    
    :param path: Path to the Parquet file to read from.
    :param batch_size: Optional batch size for reading records. If None,
                      uses the default batch size from pyarrow.
    """
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
    """
    Synchronously read dataset records from a Parquet file.
    
    This function reads records from a Parquet dataset file using pyarrow
    and yields individual records as dictionaries. It processes the file
    in batches for memory efficiency.
    
    :param path: Path to the Parquet file to read from.
    :param batch_size: Optional batch size for reading records. If None,
                      uses pyarrow's default batch size.
    """
    import pyarrow.parquet as pq  # pylint: disable=import-outside-toplevel

    # we need use kwargs method to preserve original default value
    kwargs = {}
    if batch_size is not None:
        kwargs['batch_size'] = batch_size
    with pq.ParquetFile(path) as reader:
        for batch in reader.iter_batches(**kwargs):  # type: ignore[arg-type]
            yield from batch.to_pylist()
