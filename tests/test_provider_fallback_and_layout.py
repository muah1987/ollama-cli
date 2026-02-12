"""
Tests for provider fallback routing with user-selected model override
and status bar terminal positioning (pinned to bottom).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

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
        """Session.send() should pass self.model to provider_router.route()."""
        import inspect

        from model.session import Session

        source = inspect.getsource(Session.send)
        assert "model=self.model" in source


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
