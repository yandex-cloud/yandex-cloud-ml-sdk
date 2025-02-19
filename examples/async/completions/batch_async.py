#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import itertools

import tqdm

from yandex_cloud_ml_sdk import AsyncYCloudML


def chunker(it, size):
    iterator = iter(it)
    while chunk := list(itertools.islice(iterator, size)):
        yield chunk


async def run_chunked_tasks(function, data, chunk_size, tqdm_callback=None):
    all_tasks = []
    for chunk in chunker(data, chunk_size):
        chunk_tasks = (asyncio.create_task(function(item)) for item in chunk)
        all_tasks.extend(chunk_tasks)

        if tqdm_callback:
            tqdm_callback(len(chunk))

        await asyncio.sleep(1)

    results = await asyncio.gather(*all_tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, BaseException):
            raise result

    return results


async def main() -> None:
    """
    Example of running a lot of async requests to yandexgpt with using of our SDK
    and python asyncio.

    There are further reserve for optimization,
    like making run_chunked_tasks into async generator
    and starting status polling right after the task successful creation
    without waiting for all task to create.
    But in this case, there will be additional code complication related with
    several progressbars and with maintaining the results order
    """

    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    model = sdk.models.completions('yandexgpt')

    input_data = [["foo"]] * 200

    with tqdm.tqdm(total=len(input_data), desc='creatig tasks') as t:
        operations = await run_chunked_tasks(
            function=model.run_async,
            data=input_data,
            chunk_size=100,
            tqdm_callback=t.update,
        )

    running_operations = list(enumerate(operations))
    finished_operations = []
    errors = []

    with tqdm.tqdm(total=len(running_operations), desc='finishing tasks') as t:
        while running_operations:
            statuses = await run_chunked_tasks(
                function=lambda i_op: i_op[1].get_status(),
                data=running_operations,
                chunk_size=100,
            )

            for indexed_op, status in zip(running_operations[:], statuses):
                if not status.done:
                    continue

                running_operations.remove(indexed_op)
                t.update(1)

                if status.is_succeeded:
                    finished_operations.append(indexed_op)
                else:
                    errors.append(status.error)

    sorted_operations = (op for _, op in sorted(finished_operations))
    with tqdm.tqdm(total=len(input_data), desc='fetching results') as t:
        results = await run_chunked_tasks(
            function=lambda op: op.get_result(),
            data=sorted_operations,
            chunk_size=100,
            tqdm_callback=t.update
        )

    print(f'first result: {results[0]}')


if __name__ == '__main__':
    asyncio.run(main())
