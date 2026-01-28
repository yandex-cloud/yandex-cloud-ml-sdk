# Examples

Real-world examples using the included sample files.

## Setup

### Authentication

First, set up your credentials:

```bash
# Set your folder ID
export YC_FOLDER_ID="b1g..."

# Get IAM token
export YC_IAM_TOKEN=$(yc --profile=preprod-fed iam create-token)
```

### Sample Files

The examples directory contains sample files for testing:

```bash
cd src/yandex_cloud_ml_sdk/cli/search_index
ls examples/
```

Files included:
- `readme.txt` - Plain text file
- `product_catalog.md` - Markdown documentation
- `config.json` - JSON configuration
- `utils.py` - Python source code
- `sales_data.csv` - CSV data
- `article.html` - HTML content
- `data.xml` - XML data

## Basic Examples

### Example 1: Upload All Files

Upload all example files with default settings:

```bash
vector_stores local examples --name "example-store"
```

Output:
```
Uploading files: 100%|████████████████| 7/7 [00:02<00:00, 2.45file/s]
Upload completed: 7 succeeded, 0 failed

Search index created successfully!
Search Index ID: vs_abc123xyz
Name: example-store
```

### Example 2: Only Markdown Files

Upload just markdown and text files:

```bash
vector_stores local examples \
  --pattern "*.{md,txt}" \
  --name "text-only"
```

This will upload:
- `readme.txt`
- `product_catalog.md`

### Example 3: Only Code Files

Upload code and configuration:

```bash
vector_stores local examples \
  --pattern "*.{py,json}" \
  --name "code-config"
```

This will upload:
- `utils.py` (auto-detected as text/x-python)
- `config.json` (auto-detected as application/json)

**Note:** MIME types are detected automatically by the server.

### Example 4: With Metadata

Add descriptive metadata:

```bash
vector_stores local examples \
  --name "examples-test" \
  --metadata "purpose=testing" \
  --metadata "source=cli-examples" \
  --metadata "environment=development"
```

### Example 5: Temporary Store

Create a store that expires in 24 hours:

```bash
vector_stores local examples \
  --name "temp-examples" \
  --expires-after-days 1 \
  --expires-after-anchor "created_at"
```

## Advanced Examples

### Example 6: Optimized Chunking

Use larger chunks for code documentation:

```bash
vector_stores local examples \
  --name "examples-large-chunks" \
  --max-chunk-size-tokens 1500 \
  --chunk-overlap-tokens 500
```

This is good for:
- Code files that need more context
- Technical documentation
- Long-form articles

### Example 7: Small Fast Chunks

Use smaller chunks for quick lookups:

```bash
vector_stores local examples \
  --name "examples-small-chunks" \
  --max-chunk-size-tokens 400 \
  --chunk-overlap-tokens 100
```

This is good for:
- FAQ documents
- Short snippets
- Quick reference materials

### Example 8: Verbose Output

See detailed upload progress:

```bash
vector_stores local examples \
  --name "examples-verbose" \
  -vv
```

Output shows:
```
DEBUG - Scanning directory: examples
DEBUG - Found 7 files to upload
INFO - Creating vector store...
DEBUG - Uploading file: readme.txt (id: file_001)
DEBUG - Uploading file: product_catalog.md (id: file_002)
...
```

### Example 9: JSON Output for Scripting

Get machine-readable output:

```bash
result=$(vector_stores local examples \
  --name "examples-json" \
  --format json)

echo $result | jq -r '.search_index.id'
```

Output:
```
vs_abc123xyz
```

Use in a script:

```bash
#!/bin/bash

# Create vector store
STORE_ID=$(vector_stores local examples \
  --name "automated-store" \
  --format json | jq -r '.search_index.id')

if [ $? -eq 0 ]; then
  echo "Successfully created store: $STORE_ID"
  # Use $STORE_ID for further operations
else
  echo "Failed to create store"
  exit 1
fi
```

### Example 10: Parallel Processing

Maximum performance with parallel uploads:

```bash
vector_stores local examples \
  --name "examples-fast" \
  --max-concurrent-uploads 10 \
  --skip-on-error
```

## Real-World Scenarios

### Scenario 1: Product Documentation

Upload and organize product docs from examples:

```bash
vector_stores local examples \
  --pattern "*.md" \
  --name "product-docs-2024" \
  --metadata "category=documentation" \
  --metadata "product=cloud-ml" \
  --metadata "version=2.0" \
  --metadata "language=en" \
  --expires-after-days 90 \
  --expires-after-anchor "last_active_at"
```

Use case:
- Documentation that should stay fresh
- Auto-expire after 90 days of no usage
- Easy filtering by metadata

### Scenario 2: Code Review Helper

Index code samples for AI-powered code review:

```bash
vector_stores local examples \
  --pattern "*.py" \
  --name "code-review-examples" \
  --metadata "type=code" \
  --metadata "language=python" \
  --max-chunk-size-tokens 1000 \
  --chunk-overlap-tokens 200
```

Use case:
- Larger chunks to preserve function context
- More overlap for better code understanding
- Metadata for filtering by language

### Scenario 3: Data Analysis Knowledge Base

Index data files and documentation:

```bash
vector_stores local examples \
  --pattern "*.{csv,json,md}" \
  --name "data-kb" \
  --metadata "domain=analytics" \
  --metadata "team=data-science" \
  --file-expires-after-seconds 2592000 \
  --file-expires-after-anchor "created_at"
```

Use case:
- Mixed content types
- Files expire after 30 days
- Team-specific metadata for access control

### Scenario 4: Support Bot Training

Prepare files for customer support bot:

```bash
vector_stores local examples \
  --pattern "*.{md,txt,html}" \
  --name "support-bot-training" \
  --metadata "purpose=customer-support" \
  --metadata "audience=end-users" \
  --metadata "bot=helpbot-v1" \
  --max-chunk-size-tokens 600 \
  --chunk-overlap-tokens 150
```

Use case:
- Medium-sized chunks for quick responses
- Multiple content formats
- Metadata tracks bot version

### Scenario 5: Research Assistant

Index research papers and notes:

```bash
vector_stores local examples \
  --pattern "*.{md,txt}" \
  --name "research-2024-q1" \
  --metadata "project=ml-research" \
  --metadata "quarter=2024-Q1" \
  --metadata "confidentiality=internal" \
  --expires-after-days 180 \
  --expires-after-anchor "created_at" \
  --max-chunk-size-tokens 1500 \
  --chunk-overlap-tokens 500 \
  -v
```

Use case:
- Large chunks for academic context
- Expires after 6 months
- Verbose logging for audit trail

## Testing and Validation

### Test Upload Performance

Time the upload process:

```bash
time vector_stores local examples \
  --name "perf-test" \
  --max-concurrent-uploads 8
```

### Test Different Chunk Sizes

Compare search quality with different chunking:

```bash
# Small chunks
vector_stores local examples --name "test-small" \
  --max-chunk-size-tokens 400 --chunk-overlap-tokens 100

# Medium chunks (default)
vector_stores local examples --name "test-medium" \
  --max-chunk-size-tokens 800 --chunk-overlap-tokens 400

# Large chunks
vector_stores local examples --name "test-large" \
  --max-chunk-size-tokens 1500 --chunk-overlap-tokens 500
```

Then test search quality on each store.

### Test Error Handling

See how the tool handles errors:

```bash
# Try to upload with a bad folder ID (will fail)
vector_stores local examples \
  --folder-id "invalid-id" \
  --name "error-test" \
  --skip-on-error \
  -vv
```

## Automation Scripts

### Daily Documentation Sync

```bash
#!/bin/bash
# daily-sync.sh

DATE=$(date +%Y-%m-%d)

vector_stores local examples \
  --name "docs-$DATE" \
  --metadata "sync-date=$DATE" \
  --metadata "type=daily-backup" \
  --expires-after-days 7 \
  --expires-after-anchor "created_at" \
  --format json > "store-$DATE.json"

if [ $? -eq 0 ]; then
  echo "✅ Sync completed: $DATE"
else
  echo "❌ Sync failed: $DATE"
  exit 1
fi
```

### Multi-Directory Upload

```bash
#!/bin/bash
# upload-all.sh

for dir in docs code data; do
  echo "Processing $dir..."

  vector_stores local "examples/$dir" \
    --name "$dir-store" \
    --metadata "directory=$dir" \
    --skip-on-error \
    -v
done
```

### Conditional Upload

```bash
#!/bin/bash
# conditional-upload.sh

FILE_COUNT=$(find examples -type f | wc -l)

if [ $FILE_COUNT -gt 0 ]; then
  echo "Found $FILE_COUNT files, uploading..."

  vector_stores local examples \
    --name "auto-upload-$(date +%Y%m%d)" \
    --metadata "file-count=$FILE_COUNT" \
    --skip-on-error
else
  echo "No files found, skipping upload"
fi
```

## Troubleshooting Examples

### Debug Failed Uploads

If some files fail to upload:

```bash
vector_stores local examples \
  --name "debug-test" \
  --skip-on-error \
  -vv 2>&1 | tee upload-debug.log

# Check the log for errors
grep "ERROR" upload-debug.log
```

### Test Connectivity

Verify your credentials work:

```bash
# This should succeed if auth is correct
vector_stores local examples \
  --pattern "readme.txt" \
  --name "connectivity-test"
```

### Check File Sizes

See what's being uploaded:

```bash
find examples -type f -exec ls -lh {} \; | awk '{print $5, $9}'
```

## Next Steps

After running these examples:

1. Check your vector stores in the Yandex Cloud console
2. Try searching the indexed content using the SDK
3. Experiment with different chunking strategies
4. Integrate vector stores into your applications

For more information, see:
- [README.md](./README.md) - Overview and installation
- [USAGE.md](./USAGE.md) - Detailed usage guide
- [API Documentation](https://yandex.cloud/docs/ai-studio/)
