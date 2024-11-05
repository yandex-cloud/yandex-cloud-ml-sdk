# Yandex Cloud ML SDK

This Python library provides a simple and efficient SDK for interacting with Yandex Cloud Machine Learning services. It abstracts the complexities of the raw GRPC calls, allowing developers to integrate cloud functionalities seamlessly into their applications.

## Features

- Easy-to-use interface for accessing the Yandex Cloud ML services
- Automatic handling of authentication
- Error handling and data validation for robust integration
- Support for asynchronous operations

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

## Langchain integration

To use langchain integration, install `yandex-cloud-ml-sdk` package with a `langchain` extra:

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

For more langchain integration examples look into `examples/langchain` folder.
