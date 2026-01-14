# Test Data for Search Index

This directory contains test files for the search index uploader.

## Files

- **README.md** - This file, documentation about test data
- **sample.txt** - Simple text file with sample content
- **config.json** - JSON configuration example
- **script.py** - Python script example

## Purpose

These files are used to test the local file upload functionality:
- Different MIME types (text/markdown, text/plain, application/json, text/x-python)
- Different file sizes
- Pattern matching (e.g., `*.md`, `**/*.txt`)
- Exclusion patterns

## Usage

```bash
python -m tools.search_index.cli local --directory ./test_data
```
