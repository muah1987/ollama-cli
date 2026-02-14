"""Tests for ollama_cmd CLI modules that have 0% coverage.

Each module provides a CLI command handler. We test:
- build_parser() returns a valid parser
- handle_* functions with mocked httpx calls
- Edge cases (missing args, connection errors, HTTP errors)
"""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# version.py
# ---------------------------------------------------------------------------


class TestVersionModule:
    def test_version_constant(self):
        from ollama_cmd.version import VERSION

        assert isinstance(VERSION, str)
        assert "." in VERSION

    def test_build_parser(self):
        from ollama_cmd.version import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_handle_version(self, capsys):
        from ollama_cmd.version import handle_version

        args = argparse.Namespace()
        handle_version(args)
        captured = capsys.readouterr()
        assert "cli-ollama" in captured.out


# ---------------------------------------------------------------------------
# serve.py
# ---------------------------------------------------------------------------


class TestServeModule:
    def test_build_parser(self):
        from ollama_cmd.serve import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.serve.httpx.get")
    @patch("ollama_cmd.serve.get_config")
    def test_handle_serve_success(self, mock_cfg, mock_get):
        from ollama_cmd.serve import handle_serve

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "llama3.2"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        args = argparse.Namespace()
        handle_serve(args)  # Should not raise

    @patch("ollama_cmd.serve.httpx.get", side_effect=httpx.ConnectError("fail"))
    @patch("ollama_cmd.serve.get_config")
    def test_handle_serve_connect_error(self, mock_cfg, mock_get):
        from ollama_cmd.serve import handle_serve

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        args = argparse.Namespace()
        with pytest.raises(SystemExit):
            handle_serve(args)

    @patch("ollama_cmd.serve.httpx.get")
    @patch("ollama_cmd.serve.get_config")
    def test_handle_serve_http_error(self, mock_cfg, mock_get):
        from ollama_cmd.serve import handle_serve

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        response = httpx.Response(500, request=httpx.Request("GET", "http://test"))
        mock_get.side_effect = httpx.HTTPStatusError(
            "error", request=httpx.Request("GET", "http://test"), response=response
        )
        args = argparse.Namespace()
        with pytest.raises(SystemExit):
            handle_serve(args)


# ---------------------------------------------------------------------------
# list.py
# ---------------------------------------------------------------------------


class TestListModule:
    def test_build_parser(self):
        from ollama_cmd.list import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.list.httpx.get")
    @patch("ollama_cmd.list.get_config")
    def test_handle_list_success(self, mock_cfg, mock_get):
        from ollama_cmd.list import handle_list

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {
            "models": [
                {"name": "llama3.2", "size": 4_000_000_000, "modified_at": "2025-01-01T00:00:00Z"},
                {"name": "codellama", "size": 500_000, "modified_at": "2025-06-15"},
            ]
        }
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        args = argparse.Namespace(json=False)
        handle_list(args)

    @patch("ollama_cmd.list.httpx.get")
    @patch("ollama_cmd.list.get_config")
    def test_handle_list_json_mode(self, mock_cfg, mock_get, capsys):
        from ollama_cmd.list import handle_list

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "llama3.2", "size": 1_048_576, "modified_at": "x"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(json=True)
        handle_list(args)
        captured = capsys.readouterr()
        assert "llama3.2" in captured.out

    @patch("ollama_cmd.list.httpx.get")
    @patch("ollama_cmd.list.get_config")
    def test_handle_list_empty(self, mock_cfg, mock_get):
        from ollama_cmd.list import handle_list

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(json=False)
        handle_list(args)

    @patch("ollama_cmd.list.httpx.get", side_effect=httpx.ConnectError("fail"))
    @patch("ollama_cmd.list.get_config")
    def test_handle_list_connect_error(self, mock_cfg, mock_get):
        from ollama_cmd.list import handle_list

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        args = argparse.Namespace(json=False)
        with pytest.raises(SystemExit):
            handle_list(args)


# ---------------------------------------------------------------------------
# status.py
# ---------------------------------------------------------------------------


class TestStatusModule:
    def test_build_parser(self):
        from ollama_cmd.status import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.status.httpx.get")
    @patch("ollama_cmd.status.get_config")
    def test_handle_status_server_online(self, mock_cfg, mock_get):
        from ollama_cmd.status import handle_status

        mock_cfg.return_value = MagicMock(
            ollama_host="http://localhost:11434",
            provider="ollama",
            ollama_model="llama3.2",
            context_length=4096,
            auto_compact=True,
            compact_threshold=0.85,
            hooks_enabled=True,
        )
        tags_resp = MagicMock()
        tags_resp.json.return_value = {"models": [{"name": "m1"}]}
        tags_resp.raise_for_status = MagicMock()

        ps_resp = MagicMock()
        ps_resp.json.return_value = {
            "models": [{"name": "llama3.2", "size": 2_000_000_000, "expires_at": "2025-01-01T12:00:00Z"}]
        }
        ps_resp.raise_for_status = MagicMock()
        mock_get.side_effect = [tags_resp, ps_resp]

        args = argparse.Namespace(json=False)
        handle_status(args)

    @patch("ollama_cmd.status.httpx.get")
    @patch("ollama_cmd.status.get_config")
    def test_handle_status_json(self, mock_cfg, mock_get, capsys):
        from ollama_cmd.status import handle_status

        mock_cfg.return_value = MagicMock(
            ollama_host="http://localhost:11434",
            provider="ollama",
            ollama_model="llama3.2",
            context_length=4096,
            auto_compact=False,
            compact_threshold=0.85,
            hooks_enabled=False,
        )
        mock_get.side_effect = httpx.ConnectError("fail")
        args = argparse.Namespace(json=True)
        handle_status(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["server"]["status"] == "offline"

    @patch("ollama_cmd.status.httpx.get", side_effect=httpx.ConnectError("fail"))
    @patch("ollama_cmd.status.get_config")
    def test_handle_status_server_offline(self, mock_cfg, mock_get):
        from ollama_cmd.status import handle_status

        mock_cfg.return_value = MagicMock(
            ollama_host="http://localhost:11434",
            provider="ollama",
            ollama_model="llama3.2",
            context_length=4096,
            auto_compact=True,
            compact_threshold=0.85,
            hooks_enabled=True,
        )
        args = argparse.Namespace(json=False)
        handle_status(args)


# ---------------------------------------------------------------------------
# config.py (ollama_cmd)
# ---------------------------------------------------------------------------


class TestConfigCmdModule:
    def test_build_parser(self):
        from ollama_cmd.config import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_is_sensitive_key(self):
        from ollama_cmd.config import _is_sensitive_key

        assert _is_sensitive_key("anthropic_api_key") is True
        assert _is_sensitive_key("gh_token") is True
        assert _is_sensitive_key("hf_secret") is True
        assert _is_sensitive_key("ollama_model") is False
        assert _is_sensitive_key("provider") is False

    @patch("ollama_cmd.config.get_config")
    def test_show_config_default(self, mock_cfg):
        from api.config import CliOllamaConfig
        from ollama_cmd.config import handle_config

        mock_cfg.return_value = CliOllamaConfig()
        args = argparse.Namespace(action=None, key=None, value=None, json=False)
        handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_show_config_get_action(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.ollama_model = "llama3.2"
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="get", key="ollama_model", value=None, json=False)
        handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_config_get_json(self, mock_cfg, capsys):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.ollama_model = "llama3.2"
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="get", key="ollama_model", value=None, json=True)
        handle_config(args)
        captured = capsys.readouterr()
        assert "llama3.2" in captured.out

    @patch("ollama_cmd.config.get_config")
    def test_config_get_sensitive_masked(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.anthropic_api_key = "sk-secret-123"
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="get", key="anthropic_api_key", value=None, json=False)
        handle_config(args)

    @patch("ollama_cmd.config.save_config")
    @patch("ollama_cmd.config.get_config")
    def test_config_set_string(self, mock_cfg, mock_save):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.ollama_model = "llama3.2"
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="ollama_model", value="codellama", json=False)
        handle_config(args)
        assert cfg.ollama_model == "codellama"
        mock_save.assert_called_once()

    @patch("ollama_cmd.config.get_config")
    def test_config_set_missing_value(self, mock_cfg):
        from ollama_cmd.config import handle_config

        mock_cfg.return_value = MagicMock()
        args = argparse.Namespace(action="set", key="ollama_model", value=None, json=False)
        with pytest.raises(SystemExit):
            handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_config_set_unknown_key(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock(spec=[])
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="unknown_xyz", value="val", json=False)
        with pytest.raises(SystemExit):
            handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_config_set_sensitive_key_rejected(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.anthropic_api_key = "old"
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="anthropic_api_key", value="new", json=False)
        with pytest.raises(SystemExit):
            handle_config(args)

    @patch("ollama_cmd.config.save_config")
    @patch("ollama_cmd.config.get_config")
    def test_config_set_bool(self, mock_cfg, mock_save):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.auto_compact = True
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="auto_compact", value="false", json=False)
        handle_config(args)
        assert cfg.auto_compact is False

    @patch("ollama_cmd.config.save_config")
    @patch("ollama_cmd.config.get_config")
    def test_config_set_int(self, mock_cfg, mock_save):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.context_length = 4096
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="context_length", value="8192", json=False)
        handle_config(args)
        assert cfg.context_length == 8192

    @patch("ollama_cmd.config.get_config")
    def test_config_set_int_invalid(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.context_length = 4096
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="context_length", value="not_a_number", json=False)
        with pytest.raises(SystemExit):
            handle_config(args)

    @patch("ollama_cmd.config.save_config")
    @patch("ollama_cmd.config.get_config")
    def test_config_set_float(self, mock_cfg, mock_save):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.compact_threshold = 0.85
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="compact_threshold", value="0.90", json=False)
        handle_config(args)
        assert cfg.compact_threshold == pytest.approx(0.90)

    @patch("ollama_cmd.config.get_config")
    def test_config_set_float_invalid(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.compact_threshold = 0.85
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="compact_threshold", value="bad", json=False)
        with pytest.raises(SystemExit):
            handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_config_set_list_rejected(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.allowed_tools = ["file_read"]
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="set", key="allowed_tools", value="x", json=False)
        with pytest.raises(SystemExit):
            handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_config_unknown_action(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock(spec=[])
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="bad_action", key=None, value=None, json=False)
        with pytest.raises(SystemExit):
            handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_config_action_as_key_name(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock()
        cfg.ollama_model = "test"
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="ollama_model", key=None, value=None, json=False)
        handle_config(args)

    @patch("ollama_cmd.config.get_config")
    def test_show_config_json(self, mock_cfg, capsys):
        from api.config import CliOllamaConfig
        from ollama_cmd.config import handle_config

        mock_cfg.return_value = CliOllamaConfig()
        args = argparse.Namespace(action=None, key=None, value=None, json=True)
        handle_config(args)
        captured = capsys.readouterr()
        assert "ollama" in captured.out.lower()

    @patch("ollama_cmd.config.get_config")
    def test_config_get_unknown(self, mock_cfg):
        from ollama_cmd.config import handle_config

        cfg = MagicMock(spec=[])
        mock_cfg.return_value = cfg
        args = argparse.Namespace(action="get", key="nope", value=None, json=False)
        with pytest.raises(SystemExit):
            handle_config(args)


# ---------------------------------------------------------------------------
# show.py
# ---------------------------------------------------------------------------


class TestShowModule:
    def test_build_parser(self):
        from ollama_cmd.show import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.show.httpx.get")
    @patch("ollama_cmd.show.get_config")
    def test_handle_show_no_model_lists(self, mock_cfg, mock_get):
        from ollama_cmd.show import handle_show

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "llama3.2"}, {"name": "codellama"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(model_name=None, json=False, modelfile=False)
        handle_show(args)

    @patch("ollama_cmd.show.httpx.get")
    @patch("ollama_cmd.show.get_config")
    def test_handle_show_no_model_empty(self, mock_cfg, mock_get):
        from ollama_cmd.show import handle_show

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(model_name=None, json=False, modelfile=False)
        handle_show(args)

    @patch("ollama_cmd.show.httpx.post")
    @patch("ollama_cmd.show.get_config")
    def test_handle_show_model_details(self, mock_cfg, mock_post):
        from ollama_cmd.show import handle_show

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {
            "license": "MIT",
            "modelfile": "FROM llama3.2",
            "details": {
                "format": "gguf",
                "family": "llama",
                "parameter_size": "3B",
                "quantization_level": "Q4_0",
                "architecture": "transformer",
            },
            "parameters": {"temperature": 0.7, "top_p": 0.9},
        }
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp
        args = argparse.Namespace(model_name="llama3.2", json=False, modelfile=True)
        handle_show(args)

    @patch("ollama_cmd.show.httpx.post")
    @patch("ollama_cmd.show.get_config")
    def test_handle_show_json(self, mock_cfg, mock_post, capsys):
        from ollama_cmd.show import handle_show

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"details": {}}
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp
        args = argparse.Namespace(model_name="llama3.2", json=True, modelfile=False)
        handle_show(args)
        captured = capsys.readouterr()
        assert "details" in captured.out

    @patch("ollama_cmd.show.httpx.post")
    @patch("ollama_cmd.show.get_config")
    def test_handle_show_404(self, mock_cfg, mock_post):
        from ollama_cmd.show import handle_show

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        response = httpx.Response(404, request=httpx.Request("POST", "http://test"))
        mock_post.side_effect = httpx.HTTPStatusError(
            "error", request=httpx.Request("POST", "http://test"), response=response
        )
        args = argparse.Namespace(model_name="nonexistent", json=False, modelfile=False)
        with pytest.raises(SystemExit):
            handle_show(args)


# ---------------------------------------------------------------------------
# ps.py
# ---------------------------------------------------------------------------


class TestPsModule:
    def test_build_parser(self):
        from ollama_cmd.ps import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.ps.httpx.get")
    @patch("ollama_cmd.ps.get_config")
    def test_handle_ps_with_models(self, mock_cfg, mock_get):
        from ollama_cmd.ps import handle_ps

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {
            "models": [
                {
                    "name": "llama3.2:latest",
                    "size": {"vram": 2_000_000_000},
                    "expires_at": "2025-01-01T14:30:00Z",
                },
                {
                    "name": "codellama",
                    "size": {"vram": 500_000},
                    "expires_at": "N/A",
                },
            ]
        }
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(json=False)
        handle_ps(args)

    @patch("ollama_cmd.ps.httpx.get")
    @patch("ollama_cmd.ps.get_config")
    def test_handle_ps_json(self, mock_cfg, mock_get, capsys):
        from ollama_cmd.ps import handle_ps

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "m1"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(json=True)
        handle_ps(args)
        captured = capsys.readouterr()
        assert "m1" in captured.out

    @patch("ollama_cmd.ps.httpx.get")
    @patch("ollama_cmd.ps.get_config")
    def test_handle_ps_empty(self, mock_cfg, mock_get):
        from ollama_cmd.ps import handle_ps

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(json=False)
        handle_ps(args)

    @patch("ollama_cmd.ps.httpx.get", side_effect=httpx.ConnectError("fail"))
    @patch("ollama_cmd.ps.get_config")
    def test_handle_ps_connect_error(self, mock_cfg, mock_get):
        from ollama_cmd.ps import handle_ps

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        args = argparse.Namespace(json=False)
        with pytest.raises(SystemExit):
            handle_ps(args)


# ---------------------------------------------------------------------------
# stop.py
# ---------------------------------------------------------------------------


class TestStopModule:
    def test_build_parser(self):
        from ollama_cmd.stop import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.stop.httpx.post")
    @patch("ollama_cmd.stop.httpx.get")
    @patch("ollama_cmd.stop.get_config")
    def test_handle_stop_success(self, mock_cfg, mock_get, mock_post):
        from ollama_cmd.stop import handle_stop

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        ps_resp = MagicMock()
        ps_resp.json.return_value = {"models": [{"name": "llama3.2:latest"}]}
        ps_resp.raise_for_status = MagicMock()
        mock_get.return_value = ps_resp

        gen_resp = MagicMock()
        gen_resp.status_code = 200
        gen_resp.raise_for_status = MagicMock()
        mock_post.return_value = gen_resp

        args = argparse.Namespace(model_name="llama3.2")
        handle_stop(args)

    @patch("ollama_cmd.stop.httpx.get")
    @patch("ollama_cmd.stop.get_config")
    def test_handle_stop_no_model_lists(self, mock_cfg, mock_get):
        from ollama_cmd.stop import handle_stop

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": "llama3.2"}]}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(model_name=None)
        handle_stop(args)

    @patch("ollama_cmd.stop.httpx.get")
    @patch("ollama_cmd.stop.get_config")
    def test_handle_stop_no_model_empty(self, mock_cfg, mock_get):
        from ollama_cmd.stop import handle_stop

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        resp = MagicMock()
        resp.json.return_value = {"models": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        args = argparse.Namespace(model_name=None)
        handle_stop(args)

    @patch("ollama_cmd.stop.httpx.post")
    @patch("ollama_cmd.stop.httpx.get")
    @patch("ollama_cmd.stop.get_config")
    def test_handle_stop_model_404(self, mock_cfg, mock_get, mock_post):
        from ollama_cmd.stop import handle_stop

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        ps_resp = MagicMock()
        ps_resp.json.return_value = {"models": []}
        ps_resp.raise_for_status = MagicMock()
        mock_get.return_value = ps_resp
        gen_resp = MagicMock()
        gen_resp.status_code = 404
        mock_post.return_value = gen_resp
        args = argparse.Namespace(model_name="nonexistent")
        handle_stop(args)

    @patch("ollama_cmd.stop.httpx.post")
    @patch("ollama_cmd.stop.httpx.get")
    @patch("ollama_cmd.stop.get_config")
    def test_handle_stop_model_400(self, mock_cfg, mock_get, mock_post):
        from ollama_cmd.stop import handle_stop

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        ps_resp = MagicMock()
        ps_resp.json.return_value = {"models": []}
        ps_resp.raise_for_status = MagicMock()
        mock_get.return_value = ps_resp
        gen_resp = MagicMock()
        gen_resp.status_code = 400
        mock_post.return_value = gen_resp
        args = argparse.Namespace(model_name="test")
        handle_stop(args)


# ---------------------------------------------------------------------------
# cp.py
# ---------------------------------------------------------------------------


class TestCpModule:
    def test_build_parser(self):
        from ollama_cmd.cp import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.cp.get_config")
    @pytest.mark.asyncio
    async def test_handle_cp_async_success(self, mock_cfg):
        from unittest.mock import AsyncMock

        from ollama_cmd.cp import handle_cp_async

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("ollama_cmd.cp.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            args = argparse.Namespace(source="llama3.2", destination="my-llama")
            await handle_cp_async(args)


# ---------------------------------------------------------------------------
# rm.py
# ---------------------------------------------------------------------------


class TestRmModule:
    def test_build_parser(self):
        from ollama_cmd.rm import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.rm.get_config")
    @pytest.mark.asyncio
    async def test_handle_rm_async_force(self, mock_cfg):
        from unittest.mock import AsyncMock

        from ollama_cmd.rm import handle_rm_async

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_resp)

        with patch("ollama_cmd.rm.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            args = argparse.Namespace(model_name="old-model", force=True)
            await handle_rm_async(args)


# ---------------------------------------------------------------------------
# create.py
# ---------------------------------------------------------------------------


class TestCreateModule:
    def test_build_parser(self):
        from ollama_cmd.create import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)


# ---------------------------------------------------------------------------
# run.py
# ---------------------------------------------------------------------------


class TestRunModule:
    def test_build_parser(self):
        from ollama_cmd.run import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.run.httpx.stream")
    @patch("ollama_cmd.run.get_config")
    def test_handle_run_connect_error(self, mock_cfg, mock_stream):
        from ollama_cmd.run import handle_run

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434", ollama_model="llama3.2")
        mock_stream.side_effect = httpx.ConnectError("fail")
        args = argparse.Namespace(
            prompt="hello",
            model=None,
            stream=False,
            stdin=False,
            system=None,
            temperature=None,
            top_k=None,
            top_p=None,
            max_tokens=None,
            timeout=120.0,
        )
        with pytest.raises(SystemExit):
            handle_run(args)

    @patch("ollama_cmd.run.get_config")
    def test_handle_run_no_prompt(self, mock_cfg):
        from ollama_cmd.run import handle_run

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434", ollama_model="llama3.2")
        args = argparse.Namespace(
            prompt=None,
            model=None,
            stream=False,
            stdin=False,
            system=None,
            temperature=None,
            top_k=None,
            top_p=None,
            max_tokens=None,
            timeout=120.0,
        )
        with pytest.raises(SystemExit):
            handle_run(args)


# ---------------------------------------------------------------------------
# pull.py
# ---------------------------------------------------------------------------


class TestPullModule:
    def test_build_parser(self):
        from ollama_cmd.pull import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @patch("ollama_cmd.pull.get_config")
    def test_handle_pull_no_model(self, mock_cfg):
        from ollama_cmd.pull import handle_pull

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        args = argparse.Namespace(model_name=None)
        with pytest.raises(SystemExit):
            handle_pull(args)

    @patch("ollama_cmd.pull.httpx.stream", side_effect=httpx.ConnectError("fail"))
    @patch("ollama_cmd.pull.get_config")
    def test_handle_pull_connect_error(self, mock_cfg, mock_stream):
        from ollama_cmd.pull import handle_pull

        mock_cfg.return_value = MagicMock(ollama_host="http://localhost:11434")
        args = argparse.Namespace(model_name="llama3.2")
        with pytest.raises(SystemExit):
            handle_pull(args)


# ---------------------------------------------------------------------------
# planning.py
# ---------------------------------------------------------------------------


class TestPlanningModule:
    def test_initialize_planning_mode(self):
        from ollama_cmd.planning import initialize_planning_mode

        session = MagicMock()
        session.context_manager.max_tokens = 4096
        initialize_planning_mode(session)
        assert session.context_manager.max_tokens == 8192
        assert session.verbose is True
        assert session.timeout == 300

    def test_plan_task(self):
        from ollama_cmd.planning import plan_task

        session = MagicMock()
        session.send.return_value = {"content": "step 1: do X"}
        result = plan_task(session, "add auth")
        assert result == {"content": "step 1: do X"}
        session.send.assert_called_once()

    def test_execute_planning_workflow(self, capsys):
        from ollama_cmd.planning import execute_planning_workflow

        session = MagicMock()
        session.context_manager.max_tokens = 2048
        session.send.return_value = {"content": "Plan result"}
        execute_planning_workflow(session, "build feature")
        captured = capsys.readouterr()
        assert "Planning mode activated" in captured.out
        assert "Plan result" in captured.out


# ---------------------------------------------------------------------------
# work.py
# ---------------------------------------------------------------------------


class TestWorkModule:
    def test_initialize_work_mode(self):
        from ollama_cmd.work import initialize_work_mode

        session = MagicMock()
        session.context_manager.max_tokens = 4096
        initialize_work_mode(session)
        assert session.context_manager.max_tokens == 2048
        assert session.verbose is False
        assert session.timeout == 60

    def test_execute_task(self):
        from ollama_cmd.work import execute_task

        session = MagicMock()
        session.send.return_value = {"content": "done"}
        result = execute_task(session, "fix bug")
        assert result == {"content": "done"}

    def test_execute_work_workflow(self, capsys):
        from ollama_cmd.work import execute_work_workflow

        session = MagicMock()
        session.context_manager.max_tokens = 4096
        session.send.return_value = {"content": "Work result"}
        execute_work_workflow(session, "do thing")
        captured = capsys.readouterr()
        assert "Work mode activated" in captured.out
        assert "Work result" in captured.out
