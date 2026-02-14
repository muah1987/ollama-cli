"""Tests for LlamaCppProvider, VllmProvider, OtherProvider, and their skill modules."""

from __future__ import annotations

import pytest

from api.provider_router import (
    LlamaCppProvider,
    OtherProvider,
    ProviderError,
    ProviderRouter,
    ProviderUnavailableError,
    VllmProvider,
)

# ---------------------------------------------------------------------------
# LlamaCppProvider
# ---------------------------------------------------------------------------


class TestLlamaCppProvider:
    def test_init_defaults(self):
        p = LlamaCppProvider()
        assert p.name == "llamacpp"
        assert "8080" in p._host

    def test_init_custom_host(self):
        p = LlamaCppProvider(host="http://myhost:9090")
        assert p._host == "http://myhost:9090"

    def test_init_with_api_key(self):
        p = LlamaCppProvider(api_key="test-key-123")
        assert p._api_key == "test-key-123"

    def test_init_no_api_key_ok(self):
        """llama.cpp does not require an API key."""
        p = LlamaCppProvider()
        assert p._api_key == ""

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("LLAMACPP_HOST", "http://env-host:7777")
        monkeypatch.setenv("LLAMACPP_API_KEY", "env-key")
        monkeypatch.setenv("LLAMACPP_MODEL", "my-gguf-model")
        p = LlamaCppProvider()
        assert p._host == "http://env-host:7777"
        assert p._api_key == "env-key"
        assert p._default_model == "my-gguf-model"

    def test_get_token_count(self):
        p = LlamaCppProvider()
        count = p.get_token_count("Hello world, how are you?")
        assert count > 0

    @pytest.mark.asyncio
    async def test_close(self):
        p = LlamaCppProvider()
        await p.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_health_check_fails_when_not_running(self):
        p = LlamaCppProvider(host="http://localhost:19999")
        result = await p.health_check()
        assert result is False
        await p.close()

    @pytest.mark.asyncio
    async def test_list_models_returns_empty_when_not_running(self):
        p = LlamaCppProvider(host="http://localhost:19999")
        result = await p.list_models()
        assert result == []
        await p.close()


# ---------------------------------------------------------------------------
# VllmProvider
# ---------------------------------------------------------------------------


class TestVllmProvider:
    def test_init_defaults(self):
        p = VllmProvider()
        assert p.name == "vllm"
        assert "8000" in p._host

    def test_init_custom_host(self):
        p = VllmProvider(host="http://myhost:5555")
        assert p._host == "http://myhost:5555"

    def test_init_with_api_key(self):
        p = VllmProvider(api_key="vllm-key-123")
        assert p._api_key == "vllm-key-123"

    def test_init_no_api_key_ok(self):
        """vLLM does not require an API key."""
        p = VllmProvider()
        assert p._api_key == ""

    def test_tensor_parallel_size_default(self):
        p = VllmProvider()
        assert p.tensor_parallel_size == 1

    def test_tensor_parallel_size_from_env(self, monkeypatch):
        monkeypatch.setenv("VLLM_TENSOR_PARALLEL_SIZE", "4")
        p = VllmProvider()
        assert p.tensor_parallel_size == 4

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("VLLM_HOST", "http://env-vllm:6666")
        monkeypatch.setenv("VLLM_API_KEY", "env-vllm-key")
        monkeypatch.setenv("VLLM_MODEL", "meta-llama/Llama-3.2-70B")
        p = VllmProvider()
        assert p._host == "http://env-vllm:6666"
        assert p._api_key == "env-vllm-key"
        assert p._default_model == "meta-llama/Llama-3.2-70B"

    def test_get_token_count(self):
        p = VllmProvider()
        count = p.get_token_count("Hello world")
        assert count > 0

    @pytest.mark.asyncio
    async def test_close(self):
        p = VllmProvider()
        await p.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_health_check_fails_when_not_running(self):
        p = VllmProvider(host="http://localhost:19998")
        result = await p.health_check()
        assert result is False
        await p.close()

    @pytest.mark.asyncio
    async def test_list_models_returns_empty_when_not_running(self):
        p = VllmProvider(host="http://localhost:19998")
        result = await p.list_models()
        assert result == []
        await p.close()


# ---------------------------------------------------------------------------
# OtherProvider
# ---------------------------------------------------------------------------


class TestOtherProvider:
    def test_init_with_host(self):
        p = OtherProvider(host="http://my-server:3000")
        assert p.name == "other"
        assert p._host == "http://my-server:3000"

    def test_init_no_host_raises(self, monkeypatch):
        monkeypatch.delenv("OTHER_PROVIDER_HOST", raising=False)
        with pytest.raises(ProviderUnavailableError, match="OTHER_PROVIDER_HOST"):
            OtherProvider(host="")

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("OTHER_PROVIDER_HOST", "http://env-other:4000")
        monkeypatch.setenv("OTHER_PROVIDER_API_KEY", "env-other-key")
        monkeypatch.setenv("OTHER_PROVIDER_MODEL", "custom-model")
        p = OtherProvider()
        assert p._host == "http://env-other:4000"
        assert p._api_key == "env-other-key"
        assert p._default_model == "custom-model"

    def test_init_with_empty_api_key(self):
        """API key is optional for 'other' provider."""
        p = OtherProvider(host="http://my-server:3000", api_key="")
        assert p._api_key == ""

    def test_init_with_api_key(self):
        p = OtherProvider(host="http://my-server:3000", api_key="my-key")
        assert p._api_key == "my-key"

    def test_get_token_count(self):
        p = OtherProvider(host="http://my-server:3000")
        count = p.get_token_count("Hello world")
        assert count > 0

    @pytest.mark.asyncio
    async def test_close(self):
        p = OtherProvider(host="http://my-server:3000")
        await p.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_health_check_fails_when_not_running(self):
        p = OtherProvider(host="http://localhost:19997")
        result = await p.health_check()
        assert result is False
        await p.close()

    @pytest.mark.asyncio
    async def test_list_models_returns_empty_when_not_running(self):
        p = OtherProvider(host="http://localhost:19997")
        result = await p.list_models()
        assert result == []
        await p.close()


# ---------------------------------------------------------------------------
# ProviderRouter integration
# ---------------------------------------------------------------------------


class TestProviderRouterNewProviders:
    def test_build_provider_llamacpp(self):
        router = ProviderRouter()
        p = router._build_provider("llamacpp")
        assert isinstance(p, LlamaCppProvider)

    def test_build_provider_vllm(self):
        router = ProviderRouter()
        p = router._build_provider("vllm")
        assert isinstance(p, VllmProvider)

    def test_build_provider_other_with_host(self, monkeypatch):
        monkeypatch.setenv("OTHER_PROVIDER_HOST", "http://test-host:3000")
        router = ProviderRouter()
        p = router._build_provider("other")
        assert isinstance(p, OtherProvider)

    def test_build_provider_other_no_host_raises(self, monkeypatch):
        monkeypatch.delenv("OTHER_PROVIDER_HOST", raising=False)
        router = ProviderRouter()
        with pytest.raises((ProviderError, ProviderUnavailableError)):
            router._build_provider("other")

    def test_list_available_includes_local_providers(self, monkeypatch):
        # Clear cloud keys to isolate test
        for key in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "HF_TOKEN"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv("OTHER_PROVIDER_HOST", raising=False)
        router = ProviderRouter()
        available = router.list_available_providers()
        assert "ollama" in available
        assert "llamacpp" in available
        assert "vllm" in available

    def test_list_available_includes_other_when_configured(self, monkeypatch):
        for key in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "HF_TOKEN"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("OTHER_PROVIDER_HOST", "http://my-host:3000")
        router = ProviderRouter()
        available = router.list_available_providers()
        assert "other" in available

    def test_list_available_excludes_other_when_not_configured(self, monkeypatch):
        for key in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "HF_TOKEN"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv("OTHER_PROVIDER_HOST", raising=False)
        router = ProviderRouter()
        available = router.list_available_providers()
        assert "other" not in available

    def test_fallback_chain_includes_new_providers(self):
        from api.provider_router import _FALLBACK_CHAIN

        assert "llamacpp" in _FALLBACK_CHAIN
        assert "vllm" in _FALLBACK_CHAIN
        assert "other" in _FALLBACK_CHAIN

    def test_default_models_includes_new_providers(self):
        from api.provider_router import _DEFAULT_MODELS

        assert "llamacpp" in _DEFAULT_MODELS
        assert "vllm" in _DEFAULT_MODELS
        assert "other" in _DEFAULT_MODELS


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


class TestLlamaCppSkill:
    def test_skill_attributes(self):
        from skills.llamacpp import LlamaCppSkill

        skill = LlamaCppSkill()
        assert skill.name == "llamacpp"
        assert "llama.cpp" in skill.description.lower() or "cross-platform" in skill.description.lower()

    @pytest.mark.asyncio
    async def test_skill_info_action(self):
        from skills.llamacpp import LlamaCppSkill

        skill = LlamaCppSkill()
        result = await skill.execute(action="info")
        assert result["action"] == "info"
        assert "cpu" in result["supported_backends"]
        assert "cuda" in result["supported_backends"]
        assert "metal" in result["supported_backends"]
        assert "linux" in result["platforms"]
        assert "macos" in result["platforms"]
        assert "windows" in result["platforms"]

    def test_server_init(self):
        from skills.llamacpp import LlamaCppServer

        server = LlamaCppServer()
        assert server._host == "http://localhost:8080"
        assert server.is_available is False


class TestVllmSkill:
    def test_skill_attributes(self):
        from skills.vllm import VllmSkill

        skill = VllmSkill()
        assert skill.name == "vllm"
        assert "tensor" in skill.description.lower() or "vllm" in skill.description.lower()

    @pytest.mark.asyncio
    async def test_skill_info_action(self):
        from skills.vllm import VllmSkill

        skill = VllmSkill()
        result = await skill.execute(action="info")
        assert result["action"] == "info"
        assert "tensor_parallelism" in result["features"]
        assert "continuous_batching" in result["features"]
        assert result["tensor_parallel_size"] == 1

    def test_server_init(self):
        from skills.vllm import VllmServer

        server = VllmServer()
        assert server._host == "http://localhost:8000"
        assert server.is_available is False
        assert server.tensor_parallel_size == 1

    def test_server_tensor_parallel_from_env(self, monkeypatch):
        from skills.vllm import VllmServer

        monkeypatch.setenv("VLLM_TENSOR_PARALLEL_SIZE", "8")
        server = VllmServer()
        assert server.tensor_parallel_size == 8


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestConfigNewFields:
    def test_config_has_llamacpp_fields(self):
        from api.config import CliOllamaConfig

        cfg = CliOllamaConfig()
        assert cfg.llamacpp_host == "http://localhost:8080"
        assert cfg.llamacpp_api_key == ""
        assert cfg.llamacpp_model == "default"

    def test_config_has_vllm_fields(self):
        from api.config import CliOllamaConfig

        cfg = CliOllamaConfig()
        assert cfg.vllm_host == "http://localhost:8000"
        assert cfg.vllm_api_key == ""
        assert cfg.vllm_model == "default"
        assert cfg.vllm_tensor_parallel_size == 1

    def test_config_has_other_provider_fields(self):
        from api.config import CliOllamaConfig

        cfg = CliOllamaConfig()
        assert cfg.other_provider_host == ""
        assert cfg.other_provider_api_key == ""
        assert cfg.other_provider_model == "default"

    def test_load_config_picks_up_llamacpp_env(self, monkeypatch, tmp_path):
        from api.config import load_config

        monkeypatch.setenv("LLAMACPP_HOST", "http://test:9090")
        monkeypatch.setenv("LLAMACPP_MODEL", "my-model")
        cfg = load_config(env_path=tmp_path / ".env", config_json_path=tmp_path / "config.json")
        assert cfg.llamacpp_host == "http://test:9090"
        assert cfg.llamacpp_model == "my-model"

    def test_load_config_picks_up_vllm_env(self, monkeypatch, tmp_path):
        from api.config import load_config

        monkeypatch.setenv("VLLM_HOST", "http://test-vllm:6000")
        monkeypatch.setenv("VLLM_TENSOR_PARALLEL_SIZE", "4")
        cfg = load_config(env_path=tmp_path / ".env", config_json_path=tmp_path / "config.json")
        assert cfg.vllm_host == "http://test-vllm:6000"
        assert cfg.vllm_tensor_parallel_size == 4

    def test_load_config_picks_up_other_provider_env(self, monkeypatch, tmp_path):
        from api.config import load_config

        monkeypatch.setenv("OTHER_PROVIDER_HOST", "http://my-custom:3000")
        monkeypatch.setenv("OTHER_PROVIDER_MODEL", "custom-model")
        cfg = load_config(env_path=tmp_path / ".env", config_json_path=tmp_path / "config.json")
        assert cfg.other_provider_host == "http://my-custom:3000"
        assert cfg.other_provider_model == "custom-model"
