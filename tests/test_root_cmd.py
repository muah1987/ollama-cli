"""Tests for ollama_cmd/root.py -- CLI entry point, model resolution, banner, etc."""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import httpx
import pytest


class TestRootVersion:
    def test_version_constant(self):
        from ollama_cmd.root import VERSION
        assert isinstance(VERSION, str)
        assert "." in VERSION

    @patch("ollama_cmd.root.get_config")
    def test_cmd_version(self, mock_cfg, capsys):
        from ollama_cmd.root import cmd_version
        cmd_version(argparse.Namespace())
        out = capsys.readouterr().out
        assert "ollama-cli" in out

    @patch("ollama_cmd.root.get_config")
    def test_print_banner(self, mock_cfg):
        from ollama_cmd.root import print_banner
        mock_cfg.return_value = MagicMock(
            provider="ollama",
            ollama_model="llama3.2",
            context_length=4096,
            auto_compact=True,
            compact_threshold=0.85,
        )
        print_banner()  # Should not raise


class TestFetchLocalModels:
    @patch("ollama_cmd.root.httpx.get")
    def test_fetch_success(self, mock_get):
        from ollama_cmd.root import _fetch_local_models
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "llama3.2"}, {"name": "codellama"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        result = _fetch_local_models("http://localhost:11434")
        assert "llama3.2" in result
        assert "codellama" in result

    @patch("ollama_cmd.root.httpx.get", side_effect=httpx.ConnectError("fail"))
    def test_fetch_connect_error(self, mock_get):
        from ollama_cmd.root import _fetch_local_models
        result = _fetch_local_models("http://localhost:11434")
        assert result == []

    @patch("ollama_cmd.root.httpx.get", side_effect=httpx.TimeoutException("timeout"))
    def test_fetch_timeout(self, mock_get):
        from ollama_cmd.root import _fetch_local_models
        result = _fetch_local_models("http://localhost:11434")
        assert result == []

    @patch("ollama_cmd.root.httpx.get")
    def test_fetch_empty_models(self, mock_get):
        from ollama_cmd.root import _fetch_local_models
        resp = MagicMock()
        resp.json.return_value = {"models": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        result = _fetch_local_models("http://localhost:11434")
        assert result == []


class TestResolveModel:
    @patch("ollama_cmd.root._fetch_local_models", return_value=[])
    def test_resolve_no_models(self, mock_fetch):
        from ollama_cmd.root import _resolve_model
        result = _resolve_model("llama3.2", "http://localhost:11434")
        assert result == "llama3.2"

    @patch("ollama_cmd.root._fetch_local_models", return_value=["llama3.2", "codellama"])
    def test_resolve_exact_match(self, mock_fetch):
        from ollama_cmd.root import _resolve_model
        result = _resolve_model("llama3.2", "http://localhost:11434")
        assert result == "llama3.2"

    @patch("ollama_cmd.root._fetch_local_models", return_value=["llama3.2:latest", "codellama:latest"])
    def test_resolve_partial_match(self, mock_fetch):
        from ollama_cmd.root import _resolve_model
        result = _resolve_model("llama3.2", "http://localhost:11434")
        assert result == "llama3.2:latest"

    @patch("ollama_cmd.root._fetch_local_models", return_value=["glm-5:latest"])
    def test_resolve_cloud_tag_preserved(self, mock_fetch):
        from ollama_cmd.root import _resolve_model
        result = _resolve_model("glm-5:cloud", "http://localhost:11434")
        assert result == "glm-5:cloud"

    @patch("ollama_cmd.root._fetch_local_models", return_value=["codellama:latest"])
    def test_resolve_fallback_first(self, mock_fetch):
        from ollama_cmd.root import _resolve_model
        result = _resolve_model("nonexistent", "http://localhost:11434")
        assert result == "codellama:latest"

    @patch("ollama_cmd.root._fetch_local_models", return_value=["a", "b", "c", "d", "e", "f"])
    def test_resolve_fallback_many(self, mock_fetch):
        from ollama_cmd.root import _resolve_model
        result = _resolve_model("nonexistent", "http://localhost:11434")
        assert result == "a"


class TestBuildParser:
    def test_build_parser_returns_parser(self):
        from ollama_cmd.root import build_parser
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_build_parser_has_subcommands(self):
        from ollama_cmd.root import build_parser
        parser = build_parser()
        # Should not raise when parsing valid known subcommand
        args = parser.parse_args(["version"])
        assert hasattr(args, "func") or hasattr(args, "command")


class TestCmdStubs:
    """Test that cmd_* delegates properly raise no import errors."""

    @patch("ollama_cmd.root.get_config")
    def test_cmd_config_delegates(self, mock_cfg):
        from ollama_cmd.root import cmd_config
        mock_cfg.return_value = MagicMock()
        with patch("ollama_cmd.config.handle_config"):
            cmd_config(argparse.Namespace(action=None, key=None, value=None, json=False))

    @patch("ollama_cmd.root.get_config")
    def test_cmd_status_delegates(self, mock_cfg):
        from ollama_cmd.root import cmd_status
        with patch("ollama_cmd.status.handle_status"):
            cmd_status(argparse.Namespace(json=False))

    def test_cmd_chat_delegates(self):
        from ollama_cmd.root import cmd_chat
        with patch("ollama_cmd.root.cmd_interactive"):
            cmd_chat(argparse.Namespace())


class TestCmdList:
    @patch("ollama_cmd.root.httpx.get")
    @patch("ollama_cmd.root.get_config")
    def test_cmd_list_success(self, mock_cfg, mock_get):
        from ollama_cmd.root import cmd_list
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {
            "models": [{"name": "llama3.2", "size": 4_000_000_000, "modified_at": "2025-01-01T00:00:00Z"}]
        }
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        cmd_list(argparse.Namespace(json=False))

    @patch("ollama_cmd.root.httpx.get")
    @patch("ollama_cmd.root.get_config")
    def test_cmd_list_json(self, mock_cfg, mock_get, capsys):
        from ollama_cmd.root import cmd_list
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "llama3.2", "size": 1024, "modified_at": "x"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        cmd_list(argparse.Namespace(json=True))
        assert "llama3.2" in capsys.readouterr().out

    @patch("ollama_cmd.root.httpx.get")
    @patch("ollama_cmd.root.get_config")
    def test_cmd_list_empty(self, mock_cfg, mock_get):
        from ollama_cmd.root import cmd_list
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        cmd_list(argparse.Namespace(json=False))

    @patch("ollama_cmd.root.httpx.get", side_effect=httpx.ConnectError("fail"))
    @patch("ollama_cmd.root.get_config")
    def test_cmd_list_connect_error(self, mock_cfg, mock_get):
        from ollama_cmd.root import cmd_list
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        with pytest.raises(SystemExit):
            cmd_list(argparse.Namespace(json=False))

    @patch("ollama_cmd.root.httpx.get")
    @patch("ollama_cmd.root.get_config")
    def test_cmd_list_sizes(self, mock_cfg, mock_get):
        from ollama_cmd.root import cmd_list
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {
            "models": [
                {"name": "a", "size": 2_000_000_000, "modified_at": "2025-01-01T12:00:00Z"},
                {"name": "b", "size": 500_000, "modified_at": "nodatehere"},
            ]
        }
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        cmd_list(argparse.Namespace(json=False))


class TestCmdServe:
    @patch("ollama_cmd.root.httpx.get")
    @patch("ollama_cmd.root.get_config")
    def test_cmd_serve_success(self, mock_cfg, mock_get):
        from ollama_cmd.root import cmd_serve
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "m1"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        cmd_serve(argparse.Namespace())

    @patch("ollama_cmd.root.httpx.get", side_effect=httpx.ConnectError("fail"))
    @patch("ollama_cmd.root.get_config")
    def test_cmd_serve_connect_error(self, mock_cfg, mock_get):
        from ollama_cmd.root import cmd_serve
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        with pytest.raises(SystemExit):
            cmd_serve(argparse.Namespace())

    @patch("ollama_cmd.root.httpx.get")
    @patch("ollama_cmd.root.get_config")
    def test_cmd_serve_http_error(self, mock_cfg, mock_get):
        from ollama_cmd.root import cmd_serve
        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        response = httpx.Response(500, request=httpx.Request("GET", "http://test"))
        mock_get.side_effect = httpx.HTTPStatusError("err", request=httpx.Request("GET", "http://test"), response=response)
        with pytest.raises(SystemExit):
            cmd_serve(argparse.Namespace())
