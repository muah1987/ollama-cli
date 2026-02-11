"""Pytest configuration and fixtures for ollama-cli tests."""

import sys
from pathlib import Path

# Add production folder directories to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api"))
sys.path.insert(0, str(project_root / "cmd"))
sys.path.insert(0, str(project_root / "model"))
sys.path.insert(0, str(project_root / "runner"))
sys.path.insert(0, str(project_root / "server"))
sys.path.insert(0, str(project_root / "server"))

# pytest configuration can be added here if needed
