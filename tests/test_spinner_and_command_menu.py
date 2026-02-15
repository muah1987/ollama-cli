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

        from qarin_cmd.interactive import _LlamaSpinner

        source = inspect.getsource(_LlamaSpinner._run)
        # Must contain the escape sequence that clears to end of line
        assert "\\033[K" in source or "\033[K" in source

    def test_spinner_stop_clears_line(self) -> None:
        """Spinner stop() should emit clear-line escape to remove spinner text."""
        import inspect

        from qarin_cmd.interactive import _LlamaSpinner

        source = inspect.getsource(_LlamaSpinner.stop)
        assert "\\033[K" in source or "\033[K" in source

    def test_spinner_frames_replaced_cleanly(self) -> None:
        """Capture spinner output and verify each frame starts with \\r\\033[K."""
        from qarin_cmd.interactive import _LlamaSpinner

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
        """Build spinner frames should include [qarin] branding."""
        from qarin_cmd.interactive import _LLAMA_BUILD_SPINNER

        for frame in _LLAMA_BUILD_SPINNER:
            assert "[qarin]" in frame, f"Missing branding in: {frame}"

    def test_plan_spinner_has_cli_brand(self) -> None:
        """Plan spinner frames should include [qarin] branding."""
        from qarin_cmd.interactive import _LLAMA_PLAN_SPINNER

        for frame in _LLAMA_PLAN_SPINNER:
            assert "[qarin]" in frame, f"Missing branding in: {frame}"

    def test_test_spinner_exists(self) -> None:
        """A test-specific spinner should be defined."""
        from qarin_cmd.interactive import _LLAMA_TEST_SPINNER

        assert len(_LLAMA_TEST_SPINNER) > 0
        for frame in _LLAMA_TEST_SPINNER:
            assert "[qarin]" in frame, f"Missing branding in: {frame}"


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
            "from qarin_cmd.interactive import InteractiveMode\n"
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
            "from qarin_cmd.interactive import InteractiveMode\n"
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
        from qarin_cmd.interactive import InteractiveMode

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
        """The system prompt should instruct the AI about tool calling."""
        from model.session import Session

        prompt = Session._build_system_prompt()
        assert "tool" in prompt.lower()

    def test_session_start_sets_system_message(self) -> None:
        """Session.start() should always set a system message (even without QARIN.md)."""
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
# /model command tests (model listing, switching, and provider switching)
# ---------------------------------------------------------------------------


class TestModelCommand:
    """Tests for the /model slash command (model and provider switching)."""

    def test_model_command_registered(self) -> None:
        """The /model command should be in the command table."""
        from qarin_cmd.interactive import InteractiveMode

        assert "/model" in InteractiveMode._COMMAND_TABLE

    def test_bare_model_shows_listing(self) -> None:
        """Bare /model should display model listing without error."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/model'))\n"
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

    def test_model_switches(self) -> None:
        """``/model <name>`` should switch the session model."""
        script = (
            "import asyncio\n"
            "import os\n"
            "# Enable bypass mode for autonomous operation\n"
            "os.environ['QARIN_CLI_BYPASS_PERMISSIONS'] = 'true'\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "s = Session(model='old-model', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/model new-model'))\n"
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

    def test_model_provider_switches(self) -> None:
        """``/model provider <name>`` should switch the session provider."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/model provider gemini'))\n"
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

    def test_model_provider_rejects_invalid(self) -> None:
        """``/model provider invalid`` should not change the provider."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/model provider nonexistent'))\n"
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

    def test_model_provider_no_arg_lists(self) -> None:
        """``/model provider`` with no arg should list providers without error."""
        script = (
            "import asyncio\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "s = Session(model='test', provider='ollama')\n"
            "r = InteractiveMode(s)\n"
            "result = asyncio.run(r._dispatch_command('/model provider'))\n"
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

    def test_skill_command_removed(self) -> None:
        """The /skill command should no longer be in the command table."""
        from qarin_cmd.interactive import InteractiveMode

        assert "/skill" not in InteractiveMode._COMMAND_TABLE


# ---------------------------------------------------------------------------
# /pull command and model_pull tool tests
# ---------------------------------------------------------------------------


class TestPullCommandAndTool:
    """Tests for the /pull slash command and model_pull skill tool."""

    def test_pull_command_registered(self) -> None:
        """The /pull command should be in the command table."""
        from qarin_cmd.interactive import InteractiveMode

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
        from qarin_cmd.interactive import _VALID_PROVIDERS

        assert "hf" in _VALID_PROVIDERS


# ---------------------------------------------------------------------------
# CLI flags: --model, --provider, --api
# ---------------------------------------------------------------------------


class TestCLIFlags:
    """Tests for CLI global flags."""

    def test_api_flag_accepted(self) -> None:
        """The --api flag should be accepted by the argument parser."""
        from qarin_cmd.root import build_parser

        parser = build_parser()
        args = parser.parse_args(["--api", "http://myhost:1234"])
        assert args.api == "http://myhost:1234"

    def test_model_flag_accepted(self) -> None:
        """The --model flag should be accepted by the argument parser."""
        from qarin_cmd.root import build_parser

        parser = build_parser()
        args = parser.parse_args(["--model", "codestral:latest"])
        assert args.model == "codestral:latest"

    def test_provider_flag_includes_hf(self) -> None:
        """The --provider flag should accept 'hf'."""
        from qarin_cmd.root import build_parser

        parser = build_parser()
        args = parser.parse_args(["--provider", "hf"])
        assert args.provider == "hf"

    def test_apply_global_flags_sets_api(self) -> None:
        """_apply_global_flags should set ollama_host when --api is provided."""
        import argparse

        from qarin_cmd.root import _apply_global_flags

        args = argparse.Namespace(
            model=None,
            provider=None,
            api="http://custom:9999",
            no_hooks=False,
            output_format=None,
            json=False,
            allowed_tools=None,
        )
        _apply_global_flags(args)

        from api.config import get_config

        cfg = get_config()
        assert cfg.ollama_host == "http://custom:9999"


# ---------------------------------------------------------------------------
# Orchestrator auto-allocation
# ---------------------------------------------------------------------------


class TestOrchestratorAutoAllocation:
    """Tests for chain controller model auto-allocation."""

    def test_agent_role_optimization_mapping_exists(self) -> None:
        """AGENT_ROLE_OPTIMIZATION should map all default wave agents."""
        from runner.chain_controller import AGENT_ROLE_OPTIMIZATION, DEFAULT_WAVES

        all_agents = set()
        for wave in DEFAULT_WAVES:
            all_agents.update(wave.agents)

        for agent in all_agents:
            assert agent in AGENT_ROLE_OPTIMIZATION, f"{agent} not in mapping"

    def test_auto_allocate_returns_all_roles(self) -> None:
        """auto_allocate_models should return an entry for every mapped role."""
        from model.session import Session
        from runner.chain_controller import AGENT_ROLE_OPTIMIZATION, ChainController

        s = Session(model="test-model", provider="ollama")
        ctrl = ChainController(s)
        allocations = ctrl.auto_allocate_models()

        for role in AGENT_ROLE_OPTIMIZATION:
            assert role in allocations, f"Missing allocation for {role}"

    def test_auto_allocate_defaults_to_session_model(self) -> None:
        """Without explicit agent configs, unassigned roles use the session model."""
        from model.session import Session
        from runner.chain_controller import AGENT_ROLE_OPTIMIZATION, ChainController

        s = Session(model="my-model", provider="gemini")
        ctrl = ChainController(s)
        allocations = ctrl.auto_allocate_models()

        # Every role should have a valid allocation
        for role in AGENT_ROLE_OPTIMIZATION:
            assert role in allocations, f"Missing allocation for {role}"
            prov, model = allocations[role]
            assert isinstance(prov, str) and len(prov) > 0
            assert isinstance(model, str) and len(model) > 0

    def test_ingest_calls_auto_allocate(self) -> None:
        """ingest() should populate allocations."""
        from model.session import Session
        from runner.chain_controller import ChainController

        s = Session(model="test", provider="ollama")
        ctrl = ChainController(s)
        ctrl.ingest("test prompt")

        assert len(ctrl.allocations) > 0

    def test_run_wave_uses_optimized_agent_type(self) -> None:
        """run_wave should pass the optimized agent_type, not the raw role."""
        import inspect

        from runner.chain_controller import ChainController

        source = inspect.getsource(ChainController.run_wave)
        assert "AGENT_ROLE_OPTIMIZATION" in source
        assert "optimized_type" in source


# ---------------------------------------------------------------------------
# Native tool calling tests
# ---------------------------------------------------------------------------


class TestNativeToolCalling:
    """Tests for native function-calling (tool schema, execution, agentic loop)."""

    def test_get_tools_schema_returns_list(self) -> None:
        """get_tools_schema should return a non-empty list of tool defs."""
        from skills.tools import get_tools_schema

        schema = get_tools_schema()
        assert isinstance(schema, list)
        assert len(schema) > 0

    def test_tools_schema_has_required_fields(self) -> None:
        """Each tool in the schema should have type, function.name, function.parameters."""
        from skills.tools import get_tools_schema

        for tool in get_tools_schema():
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert func["parameters"]["type"] == "object"

    def test_tools_schema_covers_core_tools(self) -> None:
        """The schema should include the core tools (file_read, shell_exec, etc.)."""
        from skills.tools import get_tools_schema

        names = [t["function"]["name"] for t in get_tools_schema()]
        assert "file_read" in names
        assert "shell_exec" in names
        assert "grep_search" in names
        assert "web_fetch" in names

    def test_execute_tool_call_file_read(self) -> None:
        """execute_tool_call should dispatch to the correct tool function."""
        import tempfile

        from skills.tools import execute_tool_call

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            f.flush()
            result = execute_tool_call("file_read", {"path": f.name})
        assert "content" in result
        assert "hello world" in result["content"]

    def test_execute_tool_call_unknown_tool(self) -> None:
        """execute_tool_call should return error for unknown tools."""
        from skills.tools import execute_tool_call

        result = execute_tool_call("nonexistent_tool", {})
        assert "error" in result

    def test_session_extract_response_ollama_format(self) -> None:
        """_extract_response should handle Ollama native format."""
        from model.session import Session

        response = {"message": {"role": "assistant", "content": "hello"}}
        content, tool_calls = Session._extract_response(response)
        assert content == "hello"
        assert tool_calls == []

    def test_session_extract_response_with_tool_calls(self) -> None:
        """_extract_response should extract tool_calls from Ollama response."""
        from model.session import Session

        response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "file_read", "arguments": {"path": "README.md"}}}],
            }
        }
        content, tool_calls = Session._extract_response(response)
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "file_read"

    def test_session_extract_response_openai_format(self) -> None:
        """_extract_response should handle OpenAI/Codex format."""
        from model.session import Session

        response = {"choices": [{"message": {"content": "answer", "tool_calls": []}}]}
        content, tool_calls = Session._extract_response(response)
        assert content == "answer"
        assert tool_calls == []

    def test_session_has_route_with_tools(self) -> None:
        """Session should have _route_with_tools method."""
        from model.session import Session

        assert hasattr(Session, "_route_with_tools")

    def test_session_has_get_tools_schema(self) -> None:
        """Session should have _get_tools_schema method."""
        from model.session import Session

        schema = Session._get_tools_schema()
        assert isinstance(schema, list)
        assert len(schema) > 0
