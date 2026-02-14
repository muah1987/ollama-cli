"""
Basic tests for cli-ollama functionality.
"""

import os

import pytest


def test_modules_exist():
    """Test that all main modules exist and can be loaded."""
    base_dir = os.path.join(os.path.dirname(__file__), "..")

    modules = [
        "api/ollama_client.py",
        "model/session.py",
        "server/hook_runner.py",
        "runner/context_manager.py",
    ]

    for module in modules:
        module_path = os.path.join(base_dir, module)
        assert os.path.exists(module_path), f"Module {module} does not exist"


def test_commands_module_exists():
    """Test that the commands module exists."""
    cmd_dir = os.path.join(os.path.dirname(__file__), "..", "ollama_cmd")
    assert os.path.exists(cmd_dir), "ollama_cmd directory does not exist"

    expected_commands = [
        "create.py",
        "pull.py",
        "rm.py",
        "cp.py",
        "run.py",
        "show.py",
        "list.py",
        "ps.py",
        "stop.py",
        "serve.py",
    ]

    for cmd in expected_commands:
        cmd_path = os.path.join(cmd_dir, cmd)
        assert os.path.exists(cmd_path), f"Command {cmd} does not exist"


@pytest.fixture()
def sample_model():
    """Return a sample model dict for testing."""
    return {
        "name": "llama3.2",
        "modified_at": "2024-01-01T00:00:00Z",
        "size": 4_000_000_000,
    }


@pytest.fixture()
def sample_generation():
    """Return a sample generation response for testing."""
    return {
        "model": "llama3.2",
        "response": "Hello! How can I help you?",
        "done": True,
    }


def test_sample_model(sample_model):
    """Test that sample model fixture works."""
    assert "name" in sample_model
    assert sample_model["name"] == "llama3.2"


def test_sample_generation(sample_generation):
    """Test that sample generation fixture works."""
    assert "model" in sample_generation
    assert "response" in sample_generation
    assert sample_generation["done"] is True
