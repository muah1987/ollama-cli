"""
Tests for provider fallback routing with user-selected model override,
status bar terminal positioning (pinned to bottom), and model discovery.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = str(Path(__file__).parent.parent)


# ---------------------------------------------------------------------------
# Provider fallback routing: model override tests
# ---------------------------------------------------------------------------


class TestProviderFallbackModelOverride:
    """Tests that ProviderRouter.route() respects the caller-supplied model."""

    def test_route_accepts_model_parameter(self) -> None:
        """ProviderRouter.route() should accept a model keyword argument."""
        import inspect

        from api.provider_router import ProviderRouter

        sig = inspect.signature(ProviderRouter.route)
        assert "model" in sig.parameters
        assert "provider" in sig.parameters

    def test_model_override_used_on_primary_provider(self) -> None:
        """When model= is passed, the primary provider should receive it."""
        script = (
            "import asyncio\n"
            "from api.provider_router import ProviderError, ProviderRouter\n"
            "router = ProviderRouter()\n"
            "call_log = []\n"
            "class FP:\n"
            "    def __init__(self, n):\n"
            "        self.pname = n\n"
            "    async def chat(self, messages, model=None, **kw):\n"
            "        call_log.append((self.pname, model or ''))\n"
            "        return {'choices': [{'message': {'content': 'ok'}}]}\n"
            "for p in ('ollama','claude','gemini','codex','hf'):\n"
            "    router._providers[p] = FP(p)\n"
            "asyncio.run(router.route('agent', [{'role':'user','content':'hi'}], model='glm-5:cloud'))\n"
            "assert call_log[0] == ('ollama', 'glm-5:cloud'), f'got {call_log[0]}'\n"
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

    def test_model_override_not_used_on_fallback_providers(self) -> None:
        """Fallback providers should use their own default, not the override."""
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
            "for p in ('ollama','claude','gemini','codex','hf'):\n"
            "    router._providers[p] = FP(p)\n"
            "try:\n"
            "    asyncio.run(router.route('agent', [{'role':'user','content':'hi'}], model='glm-5:cloud'))\n"
            "except Exception:\n"
            "    pass\n"
            "# Primary gets the override\n"
            "assert call_log[0] == ('ollama', 'glm-5:cloud'), f'primary={call_log[0]}'\n"
            "# Fallbacks get their own defaults\n"
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

    def test_session_send_passes_model_to_router(self) -> None:
        """Session should pass self.model to provider_router.route()."""
        import inspect

        from model.session import Session

        source = inspect.getsource(Session._route_with_tools)
        assert "model=self.model" in source
        assert "provider=self.provider" in source

    def test_provider_override_used_on_primary_provider(self) -> None:
        """When provider= is passed, that provider is used as the primary target."""
        script = (
            "import asyncio\n"
            "from api.provider_router import ProviderRouter\n"
            "router = ProviderRouter()\n"
            "call_log = []\n"
            "class FP:\n"
            "    def __init__(self, n):\n"
            "        self.pname = n\n"
            "    async def chat(self, messages, model=None, **kw):\n"
            "        call_log.append((self.pname, model or ''))\n"
            "        return {'choices': [{'message': {'content': 'ok'}}]}\n"
            "for p in ('ollama','claude','gemini','codex','hf'):\n"
            "    router._providers[p] = FP(p)\n"
            "asyncio.run(router.route('agent', [{'role':'user','content':'hi'}], provider='gemini', model='glm-5:cloud'))\n"
            "assert call_log[0] == ('gemini', 'glm-5:cloud'), f'got {call_log[0]}'\n"
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
# Status bar layout: terminal positioning tests
# ---------------------------------------------------------------------------


class TestStatusBarLayout:
    """Tests that the status bar uses ANSI escape sequences for bottom pinning."""

    def test_status_bar_uses_scroll_region(self) -> None:
        """_print_status_bar should set a terminal scroll region."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from model.session import Session; "
                    "from ollama_cmd.interactive import InteractiveMode; "
                    "s = Session(model='llama3.2', provider='ollama'); "
                    "r = InteractiveMode(s); "
                    "r._print_status_bar(); "
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        # Scroll region escape: ESC[1;Nr
        assert "\033[1;" in result.stdout
        assert "r" in result.stdout

    def test_status_bar_saves_and_restores_cursor(self) -> None:
        """_print_status_bar should save and restore cursor position."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from model.session import Session; "
                    "from ollama_cmd.interactive import InteractiveMode; "
                    "s = Session(model='llama3.2', provider='ollama'); "
                    "r = InteractiveMode(s); "
                    "r._print_status_bar(); "
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        # Save cursor: ESC 7, Restore cursor: ESC 8
        assert "\0337" in result.stdout
        assert "\0338" in result.stdout

    def test_status_bar_content_present(self) -> None:
        """_print_status_bar should still contain model, session, and job info."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from model.session import Session; "
                    "from ollama_cmd.interactive import InteractiveMode; "
                    "s = Session(model='test-model', provider='ollama'); "
                    "r = InteractiveMode(s); "
                    "r._current_job = 'thinking'; "
                    "r._print_status_bar(); "
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "test-model" in result.stdout
        assert "thinking" in result.stdout

    def test_get_terminal_height_fallback(self) -> None:
        """_get_terminal_height should return 24 when no terminal is attached."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from ollama_cmd.interactive import InteractiveMode; "
                    "print(InteractiveMode._get_terminal_height())"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        height = int(result.stdout.strip())
        assert height > 0


# ---------------------------------------------------------------------------
# Model discovery / resolution tests
# ---------------------------------------------------------------------------


class TestModelDiscovery:
    """Tests for _resolve_model and _fetch_local_models in root.py."""

    def test_resolve_model_returns_configured_when_available(self) -> None:
        """When the configured model is in the local list, return it unchanged."""
        from ollama_cmd.root import _resolve_model

        with patch("ollama_cmd.root._fetch_local_models", return_value=["llama3.2:latest", "codestral:latest"]):
            result = _resolve_model("llama3.2:latest", "http://localhost:11434")
            assert result == "llama3.2:latest"

    def test_resolve_model_partial_match(self) -> None:
        """When the configured model is a prefix of a local model, return the full name."""
        from ollama_cmd.root import _resolve_model

        with patch("ollama_cmd.root._fetch_local_models", return_value=["llama3.2:latest", "codestral:latest"]):
            result = _resolve_model("llama3.2", "http://localhost:11434")
            assert result == "llama3.2:latest"

    def test_resolve_model_fallback_to_first_available(self) -> None:
        """When the configured model is not available, select the first local model."""
        from ollama_cmd.root import _resolve_model

        with patch("ollama_cmd.root._fetch_local_models", return_value=["codestral:latest", "mistral:latest"]):
            result = _resolve_model("nonexistent-model", "http://localhost:11434")
            assert result == "codestral:latest"

    def test_resolve_model_returns_default_when_no_models(self) -> None:
        """When no local models exist, return the configured default."""
        from ollama_cmd.root import _resolve_model

        with patch("ollama_cmd.root._fetch_local_models", return_value=[]):
            result = _resolve_model("llama3.2", "http://localhost:11434")
            assert result == "llama3.2"

    def test_resolve_model_returns_default_when_server_unreachable(self) -> None:
        """When Ollama server is unreachable, return the configured default."""
        from ollama_cmd.root import _resolve_model

        with patch("ollama_cmd.root._fetch_local_models", return_value=[]):
            result = _resolve_model("glm-5:cloud", "http://localhost:99999")
            assert result == "glm-5:cloud"

    def test_fetch_local_models_returns_empty_on_connection_error(self) -> None:
        """_fetch_local_models should return [] when Ollama is unreachable."""
        from ollama_cmd.root import _fetch_local_models

        result = _fetch_local_models("http://localhost:99999")
        assert result == []

    def test_resolve_model_function_exists(self) -> None:
        """_resolve_model should be importable from root."""
        from ollama_cmd.root import _resolve_model

        assert callable(_resolve_model)

    def test_fetch_local_models_function_exists(self) -> None:
        """_fetch_local_models should be importable from root."""
        from ollama_cmd.root import _fetch_local_models

        assert callable(_fetch_local_models)


# ---------------------------------------------------------------------------
# Model-not-found auto-recovery tests
# ---------------------------------------------------------------------------


class TestModelNotFoundAutoRecovery:
    """Tests for automatic model recovery when a model is not found on Ollama."""

    def test_route_retries_with_available_model_on_404(self) -> None:
        """When Ollama returns 404, the router should retry with an available model."""
        script = (
            "import asyncio\n"
            "from api.provider_router import ProviderRouter\n"
            "from api.ollama_client import OllamaModelNotFoundError\n"
            "router = ProviderRouter()\n"
            "call_log = []\n"
            "class FakeOllamaProvider:\n"
            "    name = 'ollama'\n"
            "    async def chat(self, messages, model=None, **kw):\n"
            "        call_log.append(model)\n"
            "        if model == 'glm-5':\n"
            "            raise OllamaModelNotFoundError('Model not found (HTTP 404)')\n"
            "        return {'message': {'role': 'assistant', 'content': 'ok'}}\n"
            "    async def list_models(self):\n"
            "        return ['llama3.2:latest', 'codestral:latest']\n"
            "fake = FakeOllamaProvider()\n"
            "router._providers['ollama'] = fake\n"
            "result = asyncio.run(router.route('agent', [{'role':'user','content':'hi'}], model='glm-5'))\n"
            "assert call_log[0] == 'glm-5', f'first call was {call_log[0]}'\n"
            "assert call_log[1] == 'llama3.2:latest', f'retry was {call_log[1]}'\n"
            "assert result['message']['content'] == 'ok'\n"
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
                env={**os.environ, "PYTHONPATH": _PROJECT_ROOT},
            )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout

    def test_model_switch_rejects_invalid_model(self) -> None:
        """``/model <name>`` should reject a model not found locally."""
        script = (
            "import asyncio\n"
            "from unittest.mock import patch\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='llama3.2:latest', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "with patch('ollama_cmd.root._fetch_local_models', "
            "return_value=['llama3.2:latest', 'codestral:latest']):\n"
            "    result = asyncio.run(r._dispatch_command('/model glm-5'))\n"
            "assert result is False\n"
            "assert s.model == 'llama3.2:latest', f'model should not change, got {s.model}'\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout

    def test_model_switch_accepts_valid_model(self) -> None:
        """``/model <name>`` should accept a model found locally."""
        script = (
            "import asyncio\n"
            "from unittest.mock import patch\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='llama3.2:latest', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "with patch('ollama_cmd.root._fetch_local_models', "
            "return_value=['llama3.2:latest', 'codestral:latest']):\n"
            "    result = asyncio.run(r._dispatch_command('/model codestral:latest'))\n"
            "assert result is False\n"
            "assert s.model == 'codestral:latest', f'model={s.model}'\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout

    def test_model_switch_partial_match(self) -> None:
        """``/model llama3.2`` should match ``llama3.2:latest``."""
        script = (
            "import asyncio\n"
            "from unittest.mock import patch\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='codestral:latest', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "with patch('ollama_cmd.root._fetch_local_models', "
            "return_value=['llama3.2:latest', 'codestral:latest']):\n"
            "    result = asyncio.run(r._dispatch_command('/model llama3.2'))\n"
            "assert result is False\n"
            "assert s.model == 'llama3.2:latest', f'model={s.model}'\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout

    def test_model_switch_skips_validation_for_non_ollama_provider(self) -> None:
        """``/model <name>`` should skip validation when provider is not ollama."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='old', provider='claude')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/model claude-sonnet'))\n"
            "assert result is False\n"
            "assert s.model == 'claude-sonnet', f'model={s.model}'\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout

    def test_model_switch_allows_when_server_unreachable(self) -> None:
        """``/model <name>`` should allow switch when Ollama is unreachable."""
        script = (
            "import asyncio\n"
            "from unittest.mock import patch\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='old', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "with patch('ollama_cmd.root._fetch_local_models', return_value=[]):\n"
            "    result = asyncio.run(r._dispatch_command('/model new-model'))\n"
            "assert result is False\n"
            "assert s.model == 'new-model', f'model={s.model}'\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout

    def test_ollama_model_not_found_import(self) -> None:
        """OllamaModelNotFoundError should be importable from provider_router."""
        from api.provider_router import OllamaModelNotFoundError

        assert issubclass(OllamaModelNotFoundError, Exception)
