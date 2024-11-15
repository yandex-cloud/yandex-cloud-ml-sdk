# Yandex Cloud ML SDK

This Python library provides a simple and efficient software development kit (SDK) for interacting with Yandex Cloud Machine Learning services. The SDK abstracts away the complexities of raw gRPC calls, making it easier for developers to integrate cloud functionality into their applications seamlessly.

## Features

Yandex Cloud ML SDK provides an easy-to-use interface for accessing Yandex Cloud ML services. It currently supports:

- Text generation using any [supported model](https://yandex.cloud/docs/foundation-models/concepts/yandexgpt/models)
- Image generation using [YandexART](https://yandex.cloud/docs/foundation-models/concepts/yandexart/models)
- AI Assistants and file management
- Working with [embeddings](https://yandex.cloud/docs/foundation-models/concepts/embeddings)
- Classifier [models](https://cloud.yandex/docs/foundation/concepts/classifiers/models) 

Additionally, Yandex Cloud ML SDK offers:

- Automatic authentication management
- Robust error handling and data validation
- Asynchronous operation support

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
