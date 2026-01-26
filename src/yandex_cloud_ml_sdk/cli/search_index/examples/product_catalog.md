# Product Catalog

## Cloud ML Services

### YandexGPT Pro
Advanced language model for text generation and understanding.

**Features:**
- 128K token context window
- Function calling support
- Streaming responses
- Multi-language support

**Pricing:** $0.02 per 1K tokens

### YandexGPT Lite
Fast and efficient model for simple tasks.

**Features:**
- 8K token context window
- Quick response time
- Cost-effective

**Pricing:** $0.002 per 1K tokens

## Vector Search

Create semantic search indexes from your documents with automatic chunking and embedding generation.

**Supported formats:**
- PDF, DOCX, TXT
- Markdown, HTML
- JSON, XML, CSV

## Usage Examples

```python
from yandex_cloud_ml_sdk import YCloudML

sdk = YCloudML(folder_id="your-folder-id")
result = sdk.models.completions('yandexgpt').run("Hello!")
```
