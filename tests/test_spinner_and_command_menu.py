"""Tests for spinner text clearing, CLI-branded spinners, command menu,
system prompt tool awareness, and multi-format response extraction."""

import io
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = str(Path(__file__).parent.parent)


# ---------------------------------------------------------------------------
# Spinner: text clearing (no leftover characters)
# ---------------------------------------------------------------------------


class TestSpinnerClearing:
    """Tests that the llama spinner properly clears previous text."""

    def test_spinner_uses_clear_to_eol(self) -> None:
        """Spinner _run should emit \\033[K (clear to end of line) to prevent garbled text."""
        import inspect

        from ollama_cmd.interactive import _LlamaSpinner

        source = inspect.getsource(_LlamaSpinner._run)
        # Must contain the escape sequence that clears to end of line
        assert "\\033[K" in source or "\033[K" in source

    def test_spinner_stop_clears_line(self) -> None:
        """Spinner stop() should emit clear-line escape to remove spinner text."""
        import inspect

        from ollama_cmd.interactive import _LlamaSpinner

        source = inspect.getsource(_LlamaSpinner.stop)
        assert "\\033[K" in source or "\033[K" in source

    def test_spinner_frames_replaced_cleanly(self) -> None:
        """Capture spinner output and verify each frame starts with \\r\\033[K."""
        from ollama_cmd.interactive import _LlamaSpinner

        captured = io.StringIO()
        frames = ["short", "a much longer frame text here"]
        spinner = _LlamaSpinner(frames, interval=0.05)

        with patch("sys.stdout", captured):
            spinner.start()
            time.sleep(0.15)  # Let a few frames render
            spinner.stop()

        output = captured.getvalue()
        # Each frame write should include the clear-to-eol escape
        assert "\033[K" in output


# ---------------------------------------------------------------------------
# CLI-branded spinner frames
# ---------------------------------------------------------------------------


class TestCLIBrandedSpinners:
    """Tests that build/plan/test spinners include the CLI icon branding."""

    def test_build_spinner_has_cli_brand(self) -> None:
        """Build spinner frames should include [ollama-cli] branding."""
        from ollama_cmd.interactive import _LLAMA_BUILD_SPINNER

        for frame in _LLAMA_BUILD_SPINNER:
            assert "[ollama-cli]" in frame, f"Missing branding in: {frame}"
            assert "🦙" in frame, f"Missing llama icon in: {frame}"

    def test_plan_spinner_has_cli_brand(self) -> None:
        """Plan spinner frames should include [ollama-cli] branding."""
        from ollama_cmd.interactive import _LLAMA_PLAN_SPINNER

        for frame in _LLAMA_PLAN_SPINNER:
            assert "[ollama-cli]" in frame, f"Missing branding in: {frame}"
            assert "🦙" in frame, f"Missing llama icon in: {frame}"

    def test_test_spinner_exists(self) -> None:
        """A test-specific spinner should be defined."""
        from ollama_cmd.interactive import _LLAMA_TEST_SPINNER

        assert len(_LLAMA_TEST_SPINNER) > 0
        for frame in _LLAMA_TEST_SPINNER:
            assert "[ollama-cli]" in frame, f"Missing branding in: {frame}"
            assert "🦙" in frame, f"Missing llama icon in: {frame}"


# ---------------------------------------------------------------------------
# Slash command menu (bare "/" input)
# ---------------------------------------------------------------------------


class TestSlashCommandMenu:
    """Tests that typing bare '/' shows the command menu."""

    def test_bare_slash_dispatches_to_menu(self) -> None:
        """Dispatch of bare '/' should call _show_command_menu, not error."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/'))\n"
            "assert result is False, 'bare / should not exit REPL'\n"
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

    def test_command_menu_shows_categories(self) -> None:
        """_show_command_menu output should contain category headers."""
        script = (
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "r._show_command_menu()\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Session" in result.stdout
        assert "Tools" in result.stdout

    def test_show_command_menu_method_exists(self) -> None:
        """InteractiveMode should have a _show_command_menu method."""
        from ollama_cmd.interactive import InteractiveMode

        assert hasattr(InteractiveMode, "_show_command_menu")
        assert callable(getattr(InteractiveMode, "_show_command_menu"))


# ---------------------------------------------------------------------------
# System prompt: tool awareness
# ---------------------------------------------------------------------------


class TestSystemPromptToolAwareness:
    """Tests that Session builds a tool-aware system prompt."""

    def test_build_system_prompt_method_exists(self) -> None:
        """Session should have a _build_system_prompt static method."""
        from model.session import Session

        assert hasattr(Session, "_build_system_prompt")

    def test_system_prompt_mentions_tools(self) -> None:
        """The system prompt should list available tools."""
        from model.session import Session

        prompt = Session._build_system_prompt()
        assert "file_read" in prompt
        assert "shell_exec" in prompt
        assert "grep_search" in prompt

    def test_system_prompt_mentions_tool_command(self) -> None:
        """The system prompt should instruct the AI about /tool commands."""
        from model.session import Session

        prompt = Session._build_system_prompt()
        assert "/tool" in prompt

    def test_session_start_sets_system_message(self) -> None:
        """Session.start() should always set a system message (even without OLLAMA.md)."""
        import asyncio
        import os
        import tempfile

        from model.session import Session

        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                s = Session(model="test", provider="ollama")
                asyncio.run(s.start())
                assert s.context_manager.system_message is not None
                assert "AI coding assistant" in s.context_manager.system_message
            finally:
                os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Response content extraction: multi-format support
# ---------------------------------------------------------------------------


class TestResponseContentExtraction:
    """Tests that Session.send() correctly extracts content from various provider formats."""

    def test_ollama_native_format_extraction(self) -> None:
        """Ollama native format: {message: {content: ...}} should be extracted."""
        import asyncio
        from unittest.mock import AsyncMock

        from model.session import Session

        s = Session(model="test", provider="ollama")
        asyncio.run(s.start())

        mock_response = {"message": {"role": "assistant", "content": "Hello from Ollama"}}
        s.provider_router.route = AsyncMock(return_value=mock_response)

        result = asyncio.run(s.send("hi"))
        assert result["content"] == "Hello from Ollama"

    def test_openai_format_extraction(self) -> None:
        """OpenAI format: {choices: [{message: {content: ...}}]} should be extracted."""
        import asyncio
        from unittest.mock import AsyncMock

        from model.session import Session

        s = Session(model="test", provider="codex")
        asyncio.run(s.start())

        mock_response = {"choices": [{"message": {"content": "Hello from OpenAI"}}], "usage": {}}
        s.provider_router.route = AsyncMock(return_value=mock_response)

        result = asyncio.run(s.send("hi"))
        assert result["content"] == "Hello from OpenAI"

    def test_anthropic_format_extraction(self) -> None:
        """Anthropic format: {content: [{text: ...}]} should be extracted."""
        import asyncio
        from unittest.mock import AsyncMock

        from model.session import Session

        s = Session(model="test", provider="claude")
        asyncio.run(s.start())

        mock_response = {"content": [{"type": "text", "text": "Hello from Claude"}]}
        s.provider_router.route = AsyncMock(return_value=mock_response)

        result = asyncio.run(s.send("hi"))
        assert result["content"] == "Hello from Claude"

    def test_gemini_format_extraction(self) -> None:
        """Gemini format: {candidates: [{content: {parts: [{text: ...}]}}]} should be extracted."""
        import asyncio
        from unittest.mock import AsyncMock

        from model.session import Session

        s = Session(model="test", provider="gemini")
        asyncio.run(s.start())

        mock_response = {"candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]}
        s.provider_router.route = AsyncMock(return_value=mock_response)

        result = asyncio.run(s.send("hi"))
        assert result["content"] == "Hello from Gemini"

    def test_direct_content_string_extraction(self) -> None:
        """Direct content string: {content: "..."} should be extracted."""
        import asyncio
        from unittest.mock import AsyncMock

        from model.session import Session

        s = Session(model="test", provider="ollama")
        asyncio.run(s.start())

        mock_response = {"content": "Direct content string"}
        s.provider_router.route = AsyncMock(return_value=mock_response)

        result = asyncio.run(s.send("hi"))
        assert result["content"] == "Direct content string"

    def test_ollama_generate_format_extraction(self) -> None:
        """Ollama generate format: {response: "..."} should be extracted."""
        import asyncio
        from unittest.mock import AsyncMock

        from model.session import Session

        s = Session(model="test", provider="ollama")
        asyncio.run(s.start())

        mock_response = {"response": "Generated response"}
        s.provider_router.route = AsyncMock(return_value=mock_response)

        result = asyncio.run(s.send("hi"))
        assert result["content"] == "Generated response"


# ---------------------------------------------------------------------------
# /skill command tests
# ---------------------------------------------------------------------------


class TestSkillCommand:
    """Tests for the /skill slash command (model and provider switching)."""

    def test_skill_command_registered(self) -> None:
        """The /skill command should be in the command table."""
        from ollama_cmd.interactive import InteractiveMode

        assert "/skill" in InteractiveMode._COMMAND_TABLE

    def test_bare_skill_shows_menu(self) -> None:
        """Bare /skill should display the skills menu without error."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/skill'))\n"
            "assert result is False\n"
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

    def test_skill_model_switches(self) -> None:
        """``/skill model <name>`` should switch the session model."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='old-model', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/skill model new-model'))\n"
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

    def test_skill_provider_switches(self) -> None:
        """``/skill provider <name>`` should switch the session provider."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/skill provider gemini'))\n"
            "assert result is False\n"
            "assert s.provider == 'gemini', f'provider={s.provider}'\n"
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

    def test_skill_provider_rejects_invalid(self) -> None:
        """``/skill provider invalid`` should not change the provider."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/skill provider nonexistent'))\n"
            "assert result is False\n"
            "assert s.provider == 'ollama', f'provider={s.provider}'\n"
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

    def test_skill_model_no_arg_lists(self) -> None:
        """``/skill model`` with no arg should list models without error."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/skill model'))\n"
            "assert result is False\n"
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

    def test_skill_provider_no_arg_lists(self) -> None:
        """``/skill provider`` with no arg should list providers without error."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from ollama_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/skill provider'))\n"
            "assert result is False\n"
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


# ---------------------------------------------------------------------------
# /pull command and model_pull tool tests
# ---------------------------------------------------------------------------


class TestPullCommandAndTool:
    """Tests for the /pull slash command and model_pull skill tool."""

    def test_pull_command_registered(self) -> None:
        """The /pull command should be in the command table."""
        from ollama_cmd.interactive import InteractiveMode

        assert "/pull" in InteractiveMode._COMMAND_TABLE

    def test_model_pull_tool_registered(self) -> None:
        """model_pull should be in the tools registry."""
        from skills.tools import get_tool

        entry = get_tool("model_pull")
        assert entry is not None
        assert entry["risk"] == "medium"

    def test_model_pull_tool_listed(self) -> None:
        """model_pull should appear in list_tools()."""
        from skills.tools import list_tools

        names = [t["name"] for t in list_tools()]
        assert "model_pull" in names

    def test_model_pull_empty_name(self) -> None:
        """model_pull with empty name should return error."""
        from skills.tools import tool_model_pull

        result = tool_model_pull("")
        assert "error" in result

    def test_model_pull_unreachable_server(self) -> None:
        """model_pull against an unreachable server should return error."""
        import os

        old = os.environ.get("OLLAMA_HOST")
        try:
            os.environ["OLLAMA_HOST"] = "http://localhost:99999"
            from skills.tools import tool_model_pull

            result = tool_model_pull("nonexistent-model")
            assert "error" in result
        finally:
            if old is not None:
                os.environ["OLLAMA_HOST"] = old
            else:
                os.environ.pop("OLLAMA_HOST", None)

    def test_hf_in_valid_providers(self) -> None:
        """The 'hf' provider should be listed as a valid provider."""
        from ollama_cmd.interactive import _VALID_PROVIDERS

        assert "hf" in _VALID_PROVIDERS
