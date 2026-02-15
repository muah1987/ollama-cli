"""
Tests for multi-model agent configuration, status bar job tracking,
and skill→hook trigger pipeline.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

_PROJECT_ROOT = str(Path(__file__).parent.parent)


# ---------------------------------------------------------------------------
# Multi-model agent configuration tests
# ---------------------------------------------------------------------------


class TestMultiModelConfig:
    """Tests for multi-model agent configuration via settings and env vars."""

    def test_config_has_agent_models_field(self) -> None:
        """Config dataclass should have agent_models field."""
        from api.config import QarinCliConfig

        cfg = QarinCliConfig()
        assert hasattr(cfg, "agent_models")
        assert cfg.agent_models is None

    def test_config_has_hf_token_field(self) -> None:
        """Config dataclass should have hf_token field."""
        from api.config import QarinCliConfig

        cfg = QarinCliConfig()
        assert hasattr(cfg, "hf_token")
        assert cfg.hf_token == ""

    def test_config_has_gh_token_field(self) -> None:
        """Config dataclass should have gh_token field."""
        from api.config import QarinCliConfig

        cfg = QarinCliConfig()
        assert hasattr(cfg, "gh_token")
        assert cfg.gh_token == ""

    def test_load_config_reads_hf_token(self) -> None:
        """load_config should read HF_TOKEN from environment."""
        from api.config import load_config

        with patch.dict(os.environ, {"HF_TOKEN": "test-hf-token"}, clear=False):
            cfg = load_config()
            assert cfg.hf_token == "test-hf-token"

    def test_load_config_reads_gh_token(self) -> None:
        """load_config should read GH_TOKEN from environment."""
        from api.config import load_config

        with patch.dict(os.environ, {"GH_TOKEN": "test-gh-token"}, clear=False):
            cfg = load_config()
            assert cfg.gh_token == "test-gh-token"

    def test_load_config_reads_search_api_key(self) -> None:
        """load_config should read SEARCH_API_KEY from environment."""
        from api.config import load_config

        with patch.dict(os.environ, {"SEARCH_API_KEY": "test-search-key"}, clear=False):
            cfg = load_config()
            assert cfg.search_api_key == "test-search-key"

    def test_save_config_excludes_tokens(self) -> None:
        """save_config should not persist API keys or tokens."""
        from api.config import QarinCliConfig, save_config

        cfg = QarinCliConfig(
            hf_token="secret-hf",
            gh_token="secret-gh",
            anthropic_api_key="secret-anthropic",
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            save_config(cfg, path)
            with open(path) as f:
                data = json.load(f)
            assert "hf_token" not in data
            assert "gh_token" not in data
            assert "anthropic_api_key" not in data
            assert "search_api_key" not in data
        finally:
            os.unlink(path)

    def test_agent_models_loaded_from_settings(self) -> None:
        """agent_models should be loadable from settings.json."""
        from api.config import QarinCliConfig

        cfg = QarinCliConfig()
        cfg.agent_models = {
            "code": {"provider": "ollama", "model": "codestral:latest"},
            "review": {"provider": "claude", "model": "claude-sonnet"},
            "test": {"provider": "gemini", "model": "gemini-flash"},
            "plan": {"provider": "ollama", "model": "llama3.2"},
            "docs": {"provider": "hf", "model": "mistral-7b"},
        }
        assert len(cfg.agent_models) == 5
        assert cfg.agent_models["code"]["provider"] == "ollama"
        assert cfg.agent_models["review"]["provider"] == "claude"


class TestProviderRouterMultiModel:
    """Tests for multi-model agent support in provider router."""

    def test_agent_model_map_loads_code_type(self) -> None:
        """_load_agent_model_config should support the code agent type."""
        from api.provider_router import _load_agent_model_config

        with patch.dict(
            os.environ,
            {
                "QARIN_CLI_AGENT_CODE_PROVIDER": "ollama",
                "QARIN_CLI_AGENT_CODE_MODEL": "codestral:latest",
            },
            clear=False,
        ):
            config = _load_agent_model_config()
            assert "code" in config
            assert config["code"] == ("ollama", "codestral:latest")

    def test_agent_model_map_supports_extended_types(self) -> None:
        """_load_agent_model_config should support review, debug, docs, orchestrator."""
        from api.provider_router import _load_agent_model_config

        env_vars = {
            "QARIN_CLI_AGENT_REVIEW_PROVIDER": "claude",
            "QARIN_CLI_AGENT_REVIEW_MODEL": "claude-sonnet",
            "QARIN_CLI_AGENT_DEBUG_PROVIDER": "gemini",
            "QARIN_CLI_AGENT_DEBUG_MODEL": "gemini-flash",
            "QARIN_CLI_AGENT_DOCS_PROVIDER": "hf",
            "QARIN_CLI_AGENT_DOCS_MODEL": "mistral-7b",
            "QARIN_CLI_AGENT_ORCHESTRATOR_PROVIDER": "codex",
            "QARIN_CLI_AGENT_ORCHESTRATOR_MODEL": "gpt-4",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = _load_agent_model_config()
            # All extended types should be present (from env or settings)
            assert "review" in config
            assert "debug" in config
            assert "docs" in config
            assert "orchestrator" in config

    def test_set_and_get_agent_model(self) -> None:
        """ProviderRouter should support set/get of agent models."""
        from api.provider_router import ProviderRouter

        router = ProviderRouter()
        router.set_agent_model("custom_agent", "claude", "claude-sonnet")
        result = router.get_agent_model("custom_agent")
        assert result == ("claude", "claude-sonnet")


class TestProviderFallbackChain:
    """Tests for provider fallback chain using correct default models."""

    def test_fallback_uses_provider_default_model(self) -> None:
        """Fallback providers should use their own default model, not the failed provider's model."""
        script = (
            "import asyncio\n"
            "from api.provider_router import ProviderError, ProviderRouter, _DEFAULT_MODELS\n"
            "router = ProviderRouter()\n"
            "call_log = []\n"
            "class FP:\n"
            "    def __init__(self, n):\n"
            "        self.pname = n\n"
            "    async def chat(self, messages, model=None, **kw):\n"
            "        call_log.append((self.pname, model or ''))\n"
            "        raise ProviderError(self.pname)\n"
            "for p in ('ollama','llamacpp','vllm','other','claude','gemini','codex','hf'):\n"
            "    router._providers[p] = FP(p)\n"
            "try:\n"
            "    asyncio.run(router.route('agent', [{'role':'user','content':'hi'}]))\n"
            "except Exception:\n"
            "    pass\n"
            "assert call_log[0][0] == 'ollama', f'first={call_log[0]}'\n"
            "assert call_log[0][1] == _DEFAULT_MODELS['ollama']\n"
            "for pn, mu in call_log[1:]:\n"
            "    exp = _DEFAULT_MODELS.get(pn)\n"
            "    assert mu == exp, f'{pn} got {mu!r} expected {exp!r}'\n"
            "print('OK')\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            f.flush()
            result = subprocess.run(
                [sys.executable, f.name],
                capture_output=True,
                text=True,
                cwd=_PROJECT_ROOT,
            )
            os.unlink(f.name)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout

    def test_primary_provider_uses_configured_model(self) -> None:
        """The primary provider should receive the user-configured model, not a default."""
        script = (
            "import asyncio\n"
            "from api.provider_router import ProviderError, ProviderRouter, _DEFAULT_MODELS\n"
            "router = ProviderRouter()\n"
            "router._task_config['agent'] = ('ollama', 'custom-model:latest')\n"
            "call_log = []\n"
            "class FP:\n"
            "    def __init__(self, n):\n"
            "        self.pname = n\n"
            "    async def chat(self, messages, model=None, **kw):\n"
            "        call_log.append((self.pname, model or ''))\n"
            "        raise ProviderError(self.pname)\n"
            "for p in ('ollama','llamacpp','vllm','other','claude','gemini','codex','hf'):\n"
            "    router._providers[p] = FP(p)\n"
            "try:\n"
            "    asyncio.run(router.route('agent', [{'role':'user','content':'test'}]))\n"
            "except Exception:\n"
            "    pass\n"
            "assert call_log[0] == ('ollama','custom-model:latest'), f'first={call_log[0]}'\n"
            "claude_entries = [(p,m) for p,m in call_log if p == 'claude']\n"
            "assert len(claude_entries) == 1, f'claude not found in {call_log}'\n"
            "assert claude_entries[0][1] == _DEFAULT_MODELS['claude'], f'claude got {claude_entries[0][1]!r}'\n"
            "print('OK')\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            f.flush()
            result = subprocess.run(
                [sys.executable, f.name],
                capture_output=True,
                text=True,
                cwd=_PROJECT_ROOT,
            )
            os.unlink(f.name)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout


# ---------------------------------------------------------------------------
# Status bar job tracking tests (using subprocess to avoid cmd module collision)
# ---------------------------------------------------------------------------


class TestStatusBarJobTracking:
    """Tests for the bottom status bar current job tracking."""

    def test_interactive_mode_has_current_job(self) -> None:
        """InteractiveMode should have _current_job attribute."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from model.session import Session; "
                    "from qarin_cmd.interactive import InteractiveMode; "
                    "s = Session(model='llama3.2', provider='ollama'); "
                    "r = InteractiveMode(s); "
                    "print(hasattr(r, '_current_job')); "
                    "print(r._current_job)"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert lines[0] == "True"
        assert lines[1] == "idle"

    def test_status_bar_includes_job_info(self) -> None:
        """_print_status_bar should include job status info."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from model.session import Session; "
                    "from qarin_cmd.interactive import InteractiveMode; "
                    "s = Session(model='llama3.2', provider='ollama'); "
                    "r = InteractiveMode(s); "
                    "r._current_job = 'thinking'; "
                    "r._print_status_bar()"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "thinking" in result.stdout

    def test_status_bar_shows_idle(self) -> None:
        """_print_status_bar should show idle when no job is running."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from model.session import Session; "
                    "from qarin_cmd.interactive import InteractiveMode; "
                    "s = Session(model='llama3.2', provider='ollama'); "
                    "r = InteractiveMode(s); "
                    "r._current_job = 'idle'; "
                    "r._print_status_bar()"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "idle" in result.stdout


# ---------------------------------------------------------------------------
# Skill→Hook trigger pipeline tests
# ---------------------------------------------------------------------------


class TestSkillTriggerPipeline:
    """Tests for the skill→hook→.py trigger pipeline."""

    def test_fire_skill_trigger_returns_true_when_no_hooks(self) -> None:
        """fire_skill_trigger should return True when hooks are disabled."""
        from skills.tools import fire_skill_trigger

        with patch("server.hook_runner.HookRunner") as mock_runner_cls:
            mock_runner = MagicMock()
            mock_runner.is_enabled.return_value = False
            mock_runner_cls.return_value = mock_runner

            result = fire_skill_trigger("test_skill", {"param": "value"})
            assert result is True

    def test_fire_skill_trigger_allows_by_default(self) -> None:
        """fire_skill_trigger should allow when hook returns allow."""
        from skills.tools import fire_skill_trigger

        with patch("server.hook_runner.HookRunner") as mock_runner_cls:
            mock_runner = MagicMock()
            mock_runner.is_enabled.return_value = True
            mock_result = MagicMock()
            mock_result.permission_decision = "allow"
            mock_runner.run_hook.return_value = [mock_result]
            mock_runner_cls.return_value = mock_runner

            result = fire_skill_trigger("test_skill")
            assert result is True

    def test_fire_skill_trigger_denies_when_blocked(self) -> None:
        """fire_skill_trigger should return False when hook denies."""
        from skills.tools import fire_skill_trigger

        with patch("server.hook_runner.HookRunner") as mock_runner_cls:
            mock_runner = MagicMock()
            mock_runner.is_enabled.return_value = True
            mock_result = MagicMock()
            mock_result.permission_decision = "deny"
            mock_runner.run_hook.return_value = [mock_result]
            mock_runner_cls.return_value = mock_runner

            result = fire_skill_trigger("dangerous_skill")
            assert result is False

    def test_skill_trigger_hook_in_settings(self) -> None:
        """SkillTrigger should be defined in settings.json."""
        settings_path = Path(__file__).parent.parent / ".qarin" / "settings.json"
        with open(settings_path) as f:
            settings = json.load(f)

        hooks = settings.get("hooks", {})
        assert "SkillTrigger" in hooks

    def test_skill_trigger_hook_script_exists(self) -> None:
        """skill_trigger.py hook script should exist."""
        hook_path = Path(__file__).parent.parent / ".qarin" / "hooks" / "skill_trigger.py"
        assert hook_path.is_file()

    def test_agent_models_in_settings(self) -> None:
        """agent_models should be defined in settings.json with at least 5 entries."""
        settings_path = Path(__file__).parent.parent / ".qarin" / "settings.json"
        with open(settings_path) as f:
            settings = json.load(f)

        agent_models = settings.get("agent_models", {})
        assert len(agent_models) >= 5
        assert "code" in agent_models
        assert "review" in agent_models
        assert "test" in agent_models
        assert "plan" in agent_models
        assert "docs" in agent_models
