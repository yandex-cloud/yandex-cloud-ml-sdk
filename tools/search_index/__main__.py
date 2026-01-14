#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.search_index.cli import main

if __name__ == "__main__":
    main()
