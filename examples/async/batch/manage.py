#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def get_dataset(sdk):
    """
    This function represents getting or creating dataset object.

    In real life you could use just a datasets ids, for example:

    ```
    dataset = await sdk.datasets.get("some_id")

    batch_task = await model.batch.run_deferred(dataset)
    # or just
    batch_task = await model.batch.run_deferred("dataset_id")
    ```

    To get to know better how to work with datasets,
    please refer to special "datasets/" examples.
    """

    async for dataset in sdk.datasets.list(status='READY', name_pattern=NAME):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.draft_from_path(
            task_type='TextToTextGenerationRequest',
            path=local_path('completions.jsonlines'),
            upload_format='jsonlines',
            name=NAME,
        )

        dataset = await dataset_draft.upload()
        print(f'created new dataset {dataset=}')

    return dataset


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # How to run batch tasks you could read in "completions.py" example
    dataset = await get_dataset(sdk)
    model = sdk.models.completions('gemma-3-12b-it')

    batch_task_operation = await model.batch.run_deferred(dataset)
    # Look how you can restore your operation when you have its id
    batch_task_operation = await sdk.batch.get(batch_task_operation.id)
    batch_task_info = await batch_task_operation.get_task_info()
    print(f'Freshly started {batch_task_operation=} have {batch_task_info=}')

    # You can list batch task operations;
    # it is light wrapper with an operation interface, which allows you to:
    # * .wait
    # * .get_status
    # * .cancel
    # * .delete
    # * .get_task_info
    # but doesn't have any fields with task information
    async for task in sdk.batch.list_operations(status='in_progress'):
        print(f"Batch task operation object: {task}")

        # You could retrieve a result from task operations history:
        status = await task.get_status()
        if status.is_succeeded:
            result = await task.get_result()
            print(f'Found a finished task, recovering its result from task operation: {result}')

        # Task info have a lot more meta information about the task
        task_info = await task.get_task_info()
        print(f"Batch task info object: {task_info}")

    # This way you could find any "waitable" operations:
    running_operations = [
        *[op async for op in sdk.batch.list_operations(status='created')],
        *[op async for op in sdk.batch.list_operations(status='pending')],
        *[op async for op in sdk.batch.list_operations(status='in_progress')],
    ]

    print(f'Next operations are in running state: {running_operations}')

    # This way you could wait all the running operations, but I will comment this code
    # for the sake of rest of the examples:
    #
    # results = await asyncio.gather(*running_operations)

    # Or you could list batch task info objects instead:
    async for task_info in sdk.batch.list_info():
        if task_info.source_dataset_id != dataset.id:
            continue

        print(
            'Found batch task with the source_dataset_id from this example '
            f'with {task_info.status=}'
        )

        # You could retrieve a result from task info history:
        if task_info.status.is_succeeded:
            assert task_info.result_dataset_id
            result = await sdk.datasets.get(task_info.result_dataset_id)
            print(f'Found a finished task, recovering its result from task info: {result}')

        # You can transform batch task info back to batch task operation object:
        task = await sdk.batch.get(task_info)

        # This is how to cancel and delete tasks:
        # NB: at the moment of this code being wrote, you can't cancel any "running"
        # task, only those which have IN_PROGRESS status.
        # But in future you could check status.is_running in this case.
        if task_info.status.name == 'IN_PROGRESS':
            print(f'Cancelling running task {task_info.task_id}')
            await task.cancel()
        elif task_info.status.is_finished:
            print(f'Deleting finished task {task_info.task_id}')
            await task.delete()
        else:
            print(f'Nothing to do with task which have status {task_info.status.name}')


if __name__ == '__main__':
    asyncio.run(main())
