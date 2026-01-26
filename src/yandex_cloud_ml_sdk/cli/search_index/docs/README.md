# Vector Stores CLI

Command-line tool for creating OpenAI-compatible vector stores from various file sources.

## Overview

The `vector_stores` CLI tool helps you:
- Upload files from local filesystem, S3, Confluence, or MediaWiki
- Create searchable vector stores with automatic chunking
- Manage file metadata and expiration policies
- Configure chunking strategies for optimal search performance

## Installation

```bash
pip install yandex-cloud-ml-sdk
```

The CLI is available as the `vector_stores` command.

## Quick Start

Set up authentication:

```bash
export YC_FOLDER_ID="your-folder-id"
export YC_IAM_TOKEN=$(yc --profile=preprod-fed iam create-token)
```

Create a vector store from local files:

```bash
vector_stores local ./documents --name "my-docs"
```

## Supported Sources

### Local Filesystem
Upload files from your local machine:
```bash
vector_stores local <directory> [options]
```

### S3-Compatible Storage
Upload from S3 or S3-compatible storage:
```bash
vector_stores s3 --bucket <name> [options]
```

### Confluence
Export and index Confluence pages:
```bash
vector_stores confluence --url <url> --space-key <key> [options]
```

### MediaWiki
Export and index wiki pages:
```bash
vector_stores wiki --api-url <url> [options]
```

## Authentication

### Yandex Cloud

Set up authentication using environment variables:

```bash
# Set your folder ID
export YC_FOLDER_ID="b1g..."

# Get IAM token using yc CLI
export YC_IAM_TOKEN=$(yc --profile=preprod-fed iam create-token)
```

Alternative authentication methods:

```bash
# Using API key (if you have one)
export YC_API_KEY="your-api-key"

# Using OAuth token
export YC_OAUTH_TOKEN="your-oauth-token"
```

### Other Services

For S3:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

For Confluence:
```bash
export CONFLUENCE_USERNAME="your-email@example.com"
export CONFLUENCE_API_TOKEN="your-api-token"
```

## Configuration Options

### Vector Store Options

- `--name TEXT` - Vector store name
- `--metadata KEY=VALUE` - Key-value metadata (max 16 pairs, can repeat)
- `--expires-after-days INTEGER` - TTL in days
- `--expires-after-anchor [created_at|last_active_at]` - Expiration anchor point

### Chunking Strategy

- `--max-chunk-size-tokens INTEGER` - Max tokens per chunk (default: 800)
- `--chunk-overlap-tokens INTEGER` - Overlap between chunks (default: 400)

### File Options

- `--file-purpose TEXT` - File purpose (default: "assistants")
- `--file-expires-after-seconds INTEGER` - File TTL in seconds
- `--file-expires-after-anchor [created_at|last_active_at]` - File expiration anchor

**Note:** MIME types are auto-detected by the server from file content and extensions.

### Upload Behavior

- `--max-concurrent-uploads INTEGER` - Parallel upload limit (default: 4)
- `--skip-on-error` - Continue on errors instead of stopping
- `-v, --verbose` - Increase verbosity (-v for INFO, -vv for DEBUG)
- `--format [text|json]` - Output format

## Examples

See [EXAMPLES.md](./EXAMPLES.md) for detailed usage examples.

## API Compatibility

This tool is compatible with OpenAI's Vector Stores API:
- [OpenAI Vector Stores Documentation](https://platform.openai.com/docs/api-reference/vector-stores)
- [OpenAI Files API](https://platform.openai.com/docs/api-reference/files)

## Common Issues

### Authentication Failed

Regenerate your IAM token:
```bash
export YC_IAM_TOKEN=$(yc --profile=preprod-fed iam create-token)
```

If still failing, verify folder ID is correct:
```bash
yc resource-manager folder list
export YC_FOLDER_ID="b1g..."
```

For detailed authentication help, see [AUTHENTICATION.md](./AUTHENTICATION.md)

### File Upload Failed
Check file permissions and ensure files aren't too large. Use `--skip-on-error` to continue with remaining files.

### Out of Memory
Reduce `--max-concurrent-uploads` if processing many large files:
```bash
vector_stores local ./docs --max-concurrent-uploads 2
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yandex-cloud/yandex-cloud-ml-sdk/issues
- Documentation: https://yandex.cloud/docs/ai-studio/

## See Also

- [Authentication Guide](./AUTHENTICATION.md) - Complete authentication setup
- [Usage Guide](./USAGE.md) - Detailed usage patterns
- [Examples](./EXAMPLES.md) - Real-world scenarios
- [Cheatsheet](./CHEATSHEET.md) - Quick reference
- [Migration Guide](MIGRATION.md) - OpenAI API compatibility notes
