# Yandex AI Studio SDK

This Python library provides a simple and efficient software development kit (SDK) for interacting with Yandex Cloud AI Studio services. The SDK abstracts away the complexities of raw gRPC and REST calls, making it easier for developers to integrate cloud functionality into their applications seamlessly.

## Features

Yandex AI Studio SDK offers a comprehensive set of high‑level abstractions that map directly to the capabilities exposed by Yandex Cloud. The current feature set includes:

- [**Assistants**](https://yandex.cloud/docs/ai-studio/concepts/assistant/)
  - Create, list, update and delete AI assistants.
  - Create and track execution of assistant runs, retrieve logs and results.
- [**Completions**](https://yandex.cloud/docs/ai-studio/operations/generation/create-prompt)
  - Text generation (completion) models with streaming support.
  - Chat usage tracking, tool calls (function calling for example).
- [**Chat**](https://yandex.cloud/docs/ai-studio/concepts/openai-compatibility)
  - OpenAI‑compatible chat API (`sdk.chat`) designed to work seamlessly with the rest of the Yandex AI Studio SDK.
  - Send and receive messages, stream responses, and work with tool calls in a unified way.
- [**Image generation**](https://yandex.cloud/docs/ai-studio/operations/generation/yandexart-request)
  - Generate images via YandexART models.
- [**Text embeddings**](https://yandex.cloud/docs/ai-studio/concepts/embeddings)
  - Compute dense vector embeddings for arbitrary text.
- [**Text classifiers**](https://yandex.cloud/docs/ai-studio/concepts/classifier/)
  - Run multi‑class, multi‑label and binary classifiers.
- [**Files**](https://yandex.cloud/docs/ai-studio/concepts/assistant/files)
  - Upload, download, list and delete files stored in Yandex Cloud AI Studio.
- [**Threads**](https://yandex.cloud/docs/ai-studio/concepts/assistant/#content)
  - Organize conversations into threads, retrieve messages, and post new messages.
- [**Search API**](https://yandex.cloud/docs/search-api/)
  - Generative, web, image and by image search.
- [**Search indexes**](https://yandex.cloud/docs/ai-studio/concepts/assistant/search-index)
  - Create, update, delete and query text, vector and hybrid search indexes.

Also there is some cross-domain functionality for features above:
- [**Batch processing**](https://yandex.cloud/docs/ai-studio/concepts/generation/batch-processing)
  - Run long‑running batch tasks with automatic polling.
- **Tools**
  - Built‑in tools such as [Generative Search Tool](https://yandex.cloud/docs/ai-studio/concepts/assistant/tools/web-search),
    [Function Tool](https://yandex.cloud/docs/ai-studio/concepts/generation/function-call)
    and Search Index Tool that can be used in Assistants, Completions, and Chat, providing a unified way to extend functionality across the SDK.
- [**Tuning**](https://yandex.cloud/docs/ai-studio/concepts/tuning/)
  - Fine‑tune models with configurable optimizers, schedulers and other hyper‑parameters.
- [**Datasets**](https://yandex.cloud/docs/ai-studio/concepts/resources/dataset)
  - Manage dataset lifecycle, upload data, validate schemas, and perform task‑type specific operations.

Additionally, Yandex AI Studio SDK offers:
- [**Authentication**](https://yandex.cloud/docs/ai-studio/sdk/#authentication)
  - Automatic selection of authentication method (API key, IAM token, OAuth token, CLI, metadata service, etc.).
- **Error handling & retries**
  - Rich exception hierarchy, retry policies, and configurable gRPC interceptors.
- **Async & sync support**
  - Every high‑level service is available in both asynchronous and synchronous variants.
- **LangChain integration**
  - Ready‑to‑use wrappers for LangChain (`.langchain()`) with an optional extra installation.

## Installation

You can install the library via pip:

```sh
pip install yandex-ai-studio-sdk
```

## SDK Reference

[https://yandex.cloud/docs/ai-studio/sdk-ref/](https://yandex.cloud/docs/ai-studio/sdk-ref/)

## Usage

Here's a basic example of how to use the SDK:

```python
from yandex_ai_studio_sdk import AIStudio

sdk = AIStudio(folder_id="...", auth="<APIKey/IAMToken/SomethingElse>")

model = sdk.models.completions('yandexgpt')
model = model.configure(temperature=0.5)
result = model.run("foo")

for alternative in result:
    print(alternative)
```

For more usage examples look into `examples` folder.

## LangChain integration

To use LangChain integration, install `yandex-ai-studio-sdk` package with a `langchain` extra:

```sh
pip install yandex-ai-studio-sdk[langchain]
```

Usage example:

```python
from yandex_ai_studio_sdk import AIStudio
from langchain_core.messages import AIMessage, HumanMessage

sdk = AIStudio(folder_id="...", auth="<APIKey/IAMToken/SomethingElse>")

model = sdk.models.completions('yandexgpt').langchain()

langchain_result = model.invoke([
    HumanMessage(content="hello!"),
    AIMessage(content="Hi there human!"),
    HumanMessage(content="Meow!"),
])
```

For more LangChain integration examples look into `examples/langchain` folder.
