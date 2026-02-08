"""
Pytest configuration and fixtures for ollama-cli tests.
"""

import pytest


@pytest.fixture
def sample_model():
    """Sample model configuration for testing."""
    return {
        "name": "llama3.2",
        "digest": "abc123",
        "size": 4_600_000_000,
        "modified_at": "2025-02-08T00:00:00Z",
    }


@pytest.fixture
def sample_generation():
    """Sample generation response for testing."""
    return {
        "model": "llama3.2",
        "response": "This is a test response.",
        "done": True,
        "context": [1, 2, 3, 4, 5],
        "created_at": "2025-02-08T00:00:00Z",
    }