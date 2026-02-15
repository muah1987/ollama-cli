"""Tests for model/session.py -- Session class, save/load, sub-contexts."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from model.session import Session


class TestSessionInit:
    def test_init_defaults(self):
        s = Session()
        assert s.model == "llama3.2"
        assert s.provider == "ollama"
        assert s.session_id is not None
        assert len(s.session_id) == 12
        assert s.hooks_enabled is True
        assert s._message_count == 0

    def test_init_custom(self):
        s = Session(session_id="test-123", model="codellama", provider="claude")
        assert s.session_id == "test-123"
        assert s.model == "codellama"
        assert s.provider == "claude"

    def test_has_agent_comm(self):
        s = Session()
        assert hasattr(s, "agent_comm")

    def test_has_memory_layer(self):
        s = Session()
        assert hasattr(s, "memory_layer")


class TestSubContext:
    def test_create_sub_context(self):
        s = Session()
        ctx = s.create_sub_context("sub-1")
        assert ctx is not None

    def test_get_sub_context(self):
        s = Session()
        s.create_sub_context("sub-1")
        result = s.get_sub_context("sub-1")
        assert result is not None

    def test_get_sub_context_missing(self):
        s = Session()
        result = s.get_sub_context("nonexistent")
        assert result is None


class TestSessionGetStatus:
    def test_get_status_returns_dict(self):
        s = Session(model="llama3.2", provider="ollama")
        status = s.get_status()
        assert isinstance(status, dict)
        assert status["model"] == "llama3.2"
        assert status["provider"] == "ollama"
        assert "session_id" in status
        assert "context_usage" in status

    def test_get_status_includes_token_metrics(self):
        s = Session()
        status = s.get_status()
        assert "token_metrics" in status


class TestSessionSave:
    def test_save_to_default_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        s = Session(session_id="save-test")
        path = s.save()
        assert os.path.exists(path)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["session_id"] == "save-test"

    def test_save_to_custom_path(self, tmp_path):
        s = Session(session_id="save-test-2")
        custom_path = str(tmp_path / "my-session.json")
        path = s.save(custom_path)
        assert path == custom_path
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["session_id"] == "save-test-2"


class TestSessionLoad:
    def test_load_existing_session(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # First save
        s1 = Session(session_id="load-test", model="llama3.2")
        s1.context_manager.add_message("user", "hello")
        s1.save()
        # Then load
        s2 = Session.load("load-test")
        assert s2.session_id == "load-test"
        assert s2.model == "llama3.2"

    def test_load_from_path(self, tmp_path):
        s1 = Session(session_id="path-load", model="codellama")
        custom_path = str(tmp_path / "session.json")
        s1.save(custom_path)
        s2 = Session.load("path-load", path=custom_path)
        assert s2.session_id == "path-load"

    def test_load_nonexistent_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            Session.load("nonexistent-session-xyz")


class TestSessionStaticMethods:
    def test_get_tools_schema(self):
        schema = Session._get_tools_schema()
        assert isinstance(schema, list)
        assert len(schema) > 0
        for tool in schema:
            assert "name" in tool or "function" in tool

    def test_extract_response_basic(self):
        response = {"message": {"content": "Hello!"}}
        content, tool_calls = Session._extract_response(response)
        assert content == "Hello!"
        assert isinstance(tool_calls, list)

    def test_extract_response_empty(self):
        content, tool_calls = Session._extract_response({})
        assert isinstance(content, str)
        assert tool_calls == []

    def test_extract_metrics(self):
        response = {
            "prompt_eval_count": 10,
            "eval_count": 20,
            "total_duration": 1000,
        }
        metrics = Session._extract_metrics(response)
        assert isinstance(metrics, dict)

    def test_execute_tool_file_read(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "test.txt").write_text("content", encoding="utf-8")
        result = Session._execute_tool("file_read", {"path": "test.txt"})
        assert isinstance(result, dict)

    def test_execute_tool_unknown(self):
        result = Session._execute_tool("nonexistent_tool_xyz", {})
        assert isinstance(result, dict)
        assert "error" in result

    def test_build_system_prompt(self):
        prompt = Session._build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_find_qarin_md(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "QARIN.md").write_text("# Project\n", encoding="utf-8")
        result = Session._find_qarin_md()
        assert result is not None

    def test_find_qarin_md_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = Session._find_qarin_md()
        assert result is None
