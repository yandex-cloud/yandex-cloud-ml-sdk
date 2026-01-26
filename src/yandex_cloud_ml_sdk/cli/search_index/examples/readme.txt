Vector Store Examples
====================

This directory contains sample files for testing the vector_stores CLI tool.

Files included:
- readme.txt - This file
- product_catalog.md - Product documentation
- config.json - Configuration example
- utils.py - Python code sample
- sales_data.csv - Sales statistics
- article.html - HTML content
- data.xml - XML data structure

Setup:
  export YC_FOLDER_ID="b1g..."
  export YC_IAM_TOKEN=$(yc --profile=preprod-fed iam create-token)

Usage:
  vector_stores local ./examples --name "test-store"
