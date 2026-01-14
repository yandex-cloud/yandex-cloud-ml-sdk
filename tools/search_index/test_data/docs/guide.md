# User Guide

## Introduction

This guide demonstrates how nested directories are handled during file scanning.

## Features

The local file source supports:

### Recursive Scanning
- Files in subdirectories are automatically discovered
- Glob patterns like `**/*.md` match files at any depth
- Relative paths are used for exclusion pattern matching

### Pattern Matching
- Use glob patterns to filter files (e.g., `*.txt`, `**/*.py`)
- Exclude specific patterns (e.g., `*/__pycache__/*`, `*.pyc`)
- Multiple exclusion patterns can be specified

### File Filtering
- Maximum file size limits can be configured
- Files larger than the limit are skipped with a warning
- MIME type detection is automatic

## Example

```bash
# Index all markdown files recursively
python -m tools.search_index.cli local \
  --directory ./test_data \
  --pattern "**/*.md"

# Index with exclusions
python -m tools.search_index.cli local \
  --directory ./test_data \
  --exclude-pattern "*/docs/*" \
  --exclude-pattern "*.pyc"
```

## Notes

This file is located in `test_data/docs/guide.md` and should be found
by recursive scanning when using patterns like `**/*.md` or `**/*`.
