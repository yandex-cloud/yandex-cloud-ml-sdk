from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def get_answer(sdk: AsyncYCloudML, index_type) -> str:
    file_coros = (
        sdk.files.upload(filename)
        for filename in
        ['turkey_example.txt', 'maldives_example.txt']
    )
    files = await asyncio.wait(file_coros)


    operation = await sdk.search_indexes.create(files=files, index_type=index_type)
    index = await operation.wait()

    tool = SearchIndexTool(
        search_index_ids=index.id,
        max_num_results=2
    )
    assistant = await sdk.assistants.create("yandexgpt", tools=tool)

    thread = await sdk.threads.create()
    with open('search_query.txt') as f:
        await thread.write(f.read().rstrip())

    run = await assistant.run(thread)
    run = await run.wait()

    answer = run.state.completed_message.content

    try:
        for file in files:
            await sdk.files.delete(file.id)
        await sdk.search_indexes.delete(index.id)
        await sdk.assistants.delete(assistant.id)
        await sdk.threads.delete(thread.id)
    finally:
        return answer


async def main():
    sdk = AsyncYCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
        service_map={
            'ai-assistants': 'assistant.api.cloud.yandex.net'
        }
    )

    index_type = sdk.search_indexes.VectorSearchIndex(
        chunking_strategy=sdk.search_indexes.VectorSearchIndex.StaticChunkingStrategy(
            max_chunk_size_tokens=100,
            chunk_overlap_tokens=50,
        )
    )
    vector_result = await get_answer(sdk, index_type)
    print(f'Vector result: {vector_result}')

    text_result = await get_answer(
        sdk,
        sdk.search_indexes.TextSearchIndex()
    )
    print(f'Text result: {text_result}')

    # TODO: hybrid result


if __name__ == '__main__':
    asyncio.run(main())
