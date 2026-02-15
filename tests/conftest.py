"""Pytest configuration and fixtures for qarin tests."""

import sys
from pathlib import Path

# Add project root to Python path so package imports (e.g. api.config) work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Also add subpackage directories for tests that use bare imports
# (e.g. ``from token_counter import TokenCounter``)
for subdir in ("api", "qarin_cmd", "model", "runner", "server", "skills"):
    sys.path.insert(0, str(project_root / subdir))

# pytest configuration can be added here if needed
