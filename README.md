# Yandex Cloud ML SDK

This Python library provides a simple and efficient software development kit (SDK) for interacting with Yandex Cloud Machine Learning services. The SDK abstracts away the complexities of raw gRPC calls, making it easier for developers to integrate cloud functionality into their applications seamlessly.

## Features

- Easy-to-use interface for accessing the Yandex Cloud ML services.
- Automatic  authentication handling.
- Robust integration with error handling and data validation.
- Asynchronous operations support.

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
