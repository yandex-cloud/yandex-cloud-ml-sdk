from __future__ import annotations

# Upload configuration defaults
DEFAULT_MAX_WORKERS = 4
"""Default maximum number of parallel upload workers"""

DEFAULT_SKIP_ON_ERROR = True
"""Default behavior for handling upload errors"""

# Chunking strategy defaults (OpenAI-compatible)
DEFAULT_MAX_CHUNK_SIZE_TOKENS = 800
"""Default maximum chunk size in tokens (OpenAI uses 800 for auto strategy)"""

DEFAULT_CHUNK_OVERLAP_TOKENS = 400
"""Default chunk overlap in tokens (OpenAI uses 400 for auto strategy)"""

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
