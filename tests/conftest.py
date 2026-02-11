"""Pytest configuration and fixtures for ollama-cli tests."""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# pytest configuration can be added here if needed
