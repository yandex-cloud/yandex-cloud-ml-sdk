#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging(log_level="WARNING")

    gen_search_tool = sdk.tools.generative_search(
        description="Use search to provide any answer",
    )
    # Parameters for limiting search tool is match
    # with sdk.search_api.generative parameters;
    # Refer to examples/sync/search_api examples for more
    limited_gen_search_tool = sdk.tools.generative_search(
        description="Use search to provide any answer",
        host="lemanapro.ru",
    )
    query = "how much does a kilogram of nails cost?"

    # We will show you three similar requests and their results with different settings:
    # * without using of generative search tool
    # * with generative search tool, which will perform internet search
    # * with generative search tool, which will perform search at given host
    for tools, text in (
        ([], 'without using of gen search'),
        ([gen_search_tool], 'with using of gen search'),
        ([limited_gen_search_tool], 'with using of gen search limited by host'),

    ):
        if tools:
            print()
            print('*' * 80)

        # On how to work with assistants itself, refer to runs.py example file
        assistant = sdk.assistants.create('yandexgpt', temperature=0, tools=tools)
        thread = sdk.threads.create()
        try:
            thread.write(query)
            run = assistant.run(thread)
            result = run.wait()
            print(f'Result of query "{query}" {text}:\n{result.text}')
        finally:
            assistant.delete()
            thread.delete()


if __name__ == '__main__':
    main()
