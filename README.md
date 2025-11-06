# Yandex Cloud ML SDK

This Python library provides a simple and efficient software development kit (SDK) for interacting with Yandex Cloud Machine Learning services. The SDK abstracts away the complexities of raw gRPC calls, making it easier for developers to integrate cloud functionality into their applications seamlessly.

## Features

Yandex Cloud ML SDK offers a comprehensive set of high‑level abstractions that map directly to the capabilities exposed by Yandex Cloud. The current feature set (derived from the `src/` package) includes:

- **Assistants**
  - Create, list, update and delete AI assistants.
  - Asynchronous (`AsyncAssistants`) and synchronous (`Assistants`) APIs.
- **Batch processing**
  - Run long‑running batch tasks with automatic polling.
  - Async (`AsyncBatch`) and sync (`Batch`) interfaces.
- **Chat & completions**
  - Text generation (completion) models with streaming support.
  - Chat usage tracking (`ChatUsage`), tool calls, and function calling.
- **.chat domain**
  - OpenAI‑compatible chat API (`sdk.chat`) designed to work seamlessly with the rest of the Yandex Cloud ML SDK.
  - Manage threads, send and receive messages, stream responses, and work with tool calls in a unified way.
- **Image generation**
  - Generate images via YandexART models.
- **Text embeddings**
  - Compute dense vector embeddings for arbitrary text.
- **Text classifiers**
  - Train and run multi‑class, multi‑label and binary classifiers.
- **Datasets**
  - Manage dataset lifecycle, upload data, validate schemas, and perform task‑type specific operations.
- **Files**
  - Upload, download, list and delete files stored in Yandex Cloud.
- **Runs**
  - Track execution of model runs, retrieve logs and results.
- **Threads**
  - Organize conversations into threads, retrieve messages, and post new messages.
- **Search API**
  - Generative search, filters, and result handling.
- **Search indexes**
  - Create, update, delete and query text, vector and hybrid search indexes.
- **Tools**
  - Built‑in tools such as `GenerativeSearchTool`, `FunctionTool` and `SearchIndexTool` that can be used in assistants, completions, and the `.chat` domain, providing a unified way to extend functionality across the SDK.
- **Tuning**
  - Fine‑tune models with configurable optimizers, schedulers and other hyper‑parameters.
- **Authentication**
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
pip install yandex-cloud-ml-sdk
```

## Usage

Here's a basic example of how to use the SDK:

```python
from yandex_cloud_ml_sdk import YCloudML

sdk = YCloudML(folder_id="...", auth="<APIKey/IAMToken/SomethingElse>")

model = sdk.models.completions('yandexgpt')
model = model.configure(temperature=0.5)
result = model.run("foo")

for alternative in result:
    print(alternative)
```

For more usage examples look into `examples` folder.

## LangChain integration

To use LangChain integration, install `yandex-cloud-ml-sdk` package with a `langchain` extra:

```sh
pip install yandex-cloud-ml-sdk[langchain]
```

Usage example:

```python
from yandex_cloud_ml_sdk import YCloudML
from langchain_core.messages import AIMessage, HumanMessage

sdk = YCloudML(folder_id="...", auth="<APIKey/IAMToken/SomethingElse>")

model = sdk.models.completions('yandexgpt').langchain()

langchain_result = model.invoke([
    HumanMessage(content="hello!"),
    AIMessage(content="Hi there human!"),
    HumanMessage(content="Meow!"),
])
```

For more LangChain integration examples look into `examples/langchain` folder.
