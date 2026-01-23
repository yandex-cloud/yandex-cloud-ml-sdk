from __future__ import annotations

# Upload configuration defaults
DEFAULT_BATCH_SIZE = 50
"""Default number of files to upload in each batch"""

DEFAULT_MAX_WORKERS = 4
"""Default maximum number of parallel upload workers"""

DEFAULT_SKIP_ON_ERROR = True
"""Default behavior for handling upload errors"""

# Index configuration defaults
DEFAULT_INDEX_TYPE = "text"
"""Default search index type"""

DEFAULT_MAX_CHUNK_SIZE_TOKENS = 700
"""Default maximum chunk size in tokens"""

DEFAULT_CHUNK_OVERLAP_TOKENS = 300
"""Default chunk overlap in tokens"""

# File source defaults
DEFAULT_FILE_PATTERN = "**/*"
"""Default glob pattern for file matching"""

DEFAULT_RECURSIVE = True
"""Default behavior for recursive directory scanning"""

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""Log message format"""

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
"""Log date format"""

# Progress bar
PROGRESS_BAR_FORMAT = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
"""Format for tqdm progress bar"""

# Size limits
BYTES_PER_MB = 1024 * 1024
"""Bytes per megabyte for display"""
