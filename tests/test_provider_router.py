"""Tests for api/provider_router.py -- Provider classes, router, agent model config."""

from __future__ import annotations

import json
import os

import pytest

from api.provider_router import (
    ClaudeProvider,
    CodexProvider,
    GeminiProvider,
    HfProvider,
    OllamaProvider,
    ProviderAuthError,
    ProviderError,
    ProviderRouter,
    ProviderUnavailableError,
    _load_agent_model_config,
)

# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_provider_error(self):
        exc = ProviderError("test")
        assert str(exc) == "test"

    def test_provider_unavailable_error(self):
        exc = ProviderUnavailableError("offline")
        assert isinstance(exc, ProviderError)

    def test_provider_auth_error(self):
        exc = ProviderAuthError("bad key")
        assert isinstance(exc, ProviderError)


# ---------------------------------------------------------------------------
# Agent model config loading
# ---------------------------------------------------------------------------


class TestLoadAgentModelConfig:
    def test_load_from_settings_file(self, tmp_path, monkeypatch):
        settings = {
            "agent_models": {
                "code": {"provider": "ollama", "model": "codestral"},
                "review": {"provider": "claude", "model": "claude-sonnet"},
            }
        }
        settings_file = tmp_path / ".ollama" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        monkeypatch.setenv("OLLAMA_PROJECT_DIR", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        result = _load_agent_model_config()
        assert "code" in result
        assert result["code"][0] == "ollama"
        assert "codestral" in result["code"][1]
        assert result["review"][0] == "claude"

    def test_load_empty_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OLLAMA_PROJECT_DIR", str(tmp_path))
        # Clear any agent env vars
        for key in list(os.environ):
            if key.startswith("QARIN_CLI_AGENT_"):
                monkeypatch.delenv(key, raising=False)
        result = _load_agent_model_config()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# OllamaProvider
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    def test_init_defaults(self):
        p = OllamaProvider()
        assert p.name == "ollama"
        assert "11434" in p._host

    def test_init_custom_host(self):
        p = OllamaProvider(host="http://custom:8080")
        assert p._host == "http://custom:8080"

    def test_get_token_count(self):
        p = OllamaProvider()
        count = p.get_token_count("Hello world, how are you?")
        assert count > 0

    @pytest.mark.asyncio
    async def test_close(self):
        p = OllamaProvider()
        await p.close()  # Should not raise


# ---------------------------------------------------------------------------
# ClaudeProvider
# ---------------------------------------------------------------------------


class TestClaudeProvider:
    def test_init_with_key(self):
        p = ClaudeProvider(api_key="sk-test-123")
        assert p._api_key == "sk-test-123"

    def test_init_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ProviderAuthError):
            ClaudeProvider(api_key=None)

    def test_convert_messages_no_system(self):
        msgs = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        system, converted = ClaudeProvider._convert_messages(msgs)
        assert system is None
        assert len(converted) == 2

    def test_convert_messages_with_system(self):
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hello"},
        ]
        system, converted = ClaudeProvider._convert_messages(msgs)
        assert system == "You are helpful."
        assert len(converted) == 1

    def test_get_token_count(self):
        p = ClaudeProvider(api_key="test")
        count = p.get_token_count("Hello world")
        assert count > 0


# ---------------------------------------------------------------------------
# GeminiProvider
# ---------------------------------------------------------------------------


class TestGeminiProvider:
    def test_init_with_key(self):
        p = GeminiProvider(api_key="test-gemini-key")
        assert p._api_key == "test-gemini-key"

    def test_init_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(ProviderAuthError):
            GeminiProvider(api_key=None)

    def test_convert_messages(self):
        msgs = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        system, converted = GeminiProvider._convert_messages(msgs)
        assert system == "System prompt"
        assert len(converted) == 2
        assert converted[0]["role"] == "user"
        assert converted[1]["role"] == "model"  # Gemini uses "model" not "assistant"


# ---------------------------------------------------------------------------
# CodexProvider
# ---------------------------------------------------------------------------


class TestCodexProvider:
    def test_init_with_key(self):
        p = CodexProvider(api_key="sk-openai-123")
        assert p._api_key == "sk-openai-123"

    def test_init_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ProviderAuthError):
            CodexProvider(api_key=None)


# ---------------------------------------------------------------------------
# HfProvider
# ---------------------------------------------------------------------------


class TestHfProvider:
    def test_init_with_key(self):
        p = HfProvider(api_key="hf_test_123")
        assert p._api_key == "hf_test_123"

    def test_init_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with pytest.raises(ProviderAuthError):
            HfProvider(api_key=None)


# ---------------------------------------------------------------------------
# ProviderRouter
# ---------------------------------------------------------------------------


class TestProviderRouter:
    def test_init(self):
        router = ProviderRouter()
        assert router is not None

    def test_set_agent_model(self):
        router = ProviderRouter()
        router.set_agent_model("code", "ollama", "codestral")
        result = router.get_agent_model("code")
        assert result == ("ollama", "codestral")

    def test_get_agent_model_missing(self):
        router = ProviderRouter()
        result = router.get_agent_model("nonexistent")
        assert result is None

    def test_build_provider_ollama(self):
        router = ProviderRouter()
        p = router._build_provider("ollama")
        assert isinstance(p, OllamaProvider)

    def test_build_provider_claude(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        router = ProviderRouter()
        p = router._build_provider("claude")
        assert isinstance(p, ClaudeProvider)

    def test_build_provider_gemini(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        router = ProviderRouter()
        p = router._build_provider("gemini")
        assert isinstance(p, GeminiProvider)

    def test_build_provider_codex(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        router = ProviderRouter()
        p = router._build_provider("codex")
        assert isinstance(p, CodexProvider)

    def test_build_provider_hf(self, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "test-key")
        router = ProviderRouter()
        p = router._build_provider("hf")
        assert isinstance(p, HfProvider)

    def test_build_provider_unknown(self):
        router = ProviderRouter()
        with pytest.raises(ProviderError):
            router._build_provider("unknown_provider")
