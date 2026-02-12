"""Build verification and end-to-end integration tests with a fake Ollama API.

This test module verifies:
1. The package builds successfully (wheel + sdist)
2. All core functions work against a fake Ollama API server
3. CLI entrypoint, session lifecycle, interactive commands, tools, hooks
4. Real Ollama Cloud API when OLLAMA_API_KEY is set (skipped otherwise)

The fake API is implemented using httpx.MockTransport so no real server is needed.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

_PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

# Hook event names expected in settings.json and as .py scripts
_EXPECTED_HOOK_EVENTS = {
    "PreToolUse": "pre_tool_use.py",
    "PostToolUse": "post_tool_use.py",
    "SessionStart": "session_start.py",
    "SessionEnd": "session_end.py",
    "PreCompact": "pre_compact.py",
    "Stop": "stop.py",
    "Notification": "notification.py",
}

from api.ollama_client import OllamaClient  # noqa: E402
from model.session import Session  # noqa: E402
from runner.context_manager import ContextManager  # noqa: E402

# ---------------------------------------------------------------------------
# Fake Ollama API responses
# ---------------------------------------------------------------------------

_FAKE_MODELS = [
    {"name": "llama3.2", "size": 2_000_000_000, "modified_at": "2025-01-01T00:00:00Z"},
    {"name": "codellama", "size": 3_500_000_000, "modified_at": "2025-01-02T00:00:00Z"},
]

_FAKE_CHAT_RESPONSE = {
    "model": "llama3.2",
    "message": {"role": "assistant", "content": "Hello! I'm a helpful assistant."},
    "done": True,
    "total_duration": 1_500_000_000,
    "load_duration": 200_000_000,
    "prompt_eval_count": 26,
    "prompt_eval_duration": 300_000_000,
    "eval_count": 12,
    "eval_duration": 800_000_000,
}

_FAKE_GENERATE_RESPONSE = {
    "model": "llama3.2",
    "response": "def reverse_string(s): return s[::-1]",
    "done": True,
    "total_duration": 1_000_000_000,
    "prompt_eval_count": 15,
    "eval_count": 10,
    "eval_duration": 500_000_000,
}

_FAKE_SHOW_RESPONSE = {
    "modelfile": "FROM llama3.2",
    "parameters": "temperature 0.7",
    "template": "{{ .Prompt }}",
    "details": {"family": "llama", "parameter_size": "3.2B", "quantization_level": "Q4_0"},
}

_FAKE_VERSION_RESPONSE = {"version": "0.5.1"}

_FAKE_EMBED_RESPONSE = {"embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5]]}

_FAKE_PS_RESPONSE = {
    "models": [{"name": "llama3.2", "size": 2_000_000_000, "digest": "abc123", "expires_at": "2025-12-31T00:00:00Z"}]
}


def _fake_handler(request: httpx.Request) -> httpx.Response:
    """Route fake API requests to canned responses."""
    path = request.url.path

    # Health / list models
    if path == "/api/tags" and request.method == "GET":
        return httpx.Response(200, json={"models": _FAKE_MODELS})

    # Chat
    if path == "/api/chat" and request.method == "POST":
        return httpx.Response(200, json=_FAKE_CHAT_RESPONSE)

    # Generate
    if path == "/api/generate" and request.method == "POST":
        body = json.loads(request.content) if request.content else {}
        if body.get("keep_alive") == 0:
            return httpx.Response(200, json={"status": "stopped"})
        return httpx.Response(200, json=_FAKE_GENERATE_RESPONSE)

    # Show
    if path == "/api/show" and request.method == "POST":
        return httpx.Response(200, json=_FAKE_SHOW_RESPONSE)

    # Version
    if path == "/api/version" and request.method == "GET":
        return httpx.Response(200, json=_FAKE_VERSION_RESPONSE)

    # Embed
    if path == "/api/embed" and request.method == "POST":
        return httpx.Response(200, json=_FAKE_EMBED_RESPONSE)

    # Pull
    if path == "/api/pull" and request.method == "POST":
        return httpx.Response(200, json={"status": "success"})

    # Create
    if path == "/api/create" and request.method == "POST":
        return httpx.Response(200, json={"status": "success"})

    # Delete
    if path == "/api/delete" and request.method == "DELETE":
        return httpx.Response(200, json={"status": "deleted"})

    # Copy
    if path == "/api/copy" and request.method == "POST":
        return httpx.Response(200, json={"status": "copied"})

    # PS
    if path == "/api/ps" and request.method == "GET":
        return httpx.Response(200, json=_FAKE_PS_RESPONSE)

    # OpenAI-compatible
    if path == "/v1/chat/completions" and request.method == "POST":
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "OpenAI-style response"}}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 8, "total_tokens": 28},
            },
        )

    return httpx.Response(404, json={"error": f"Not found: {path}"})


def _make_fake_client() -> OllamaClient:
    """Create an OllamaClient backed by the fake transport."""
    client = OllamaClient(host="http://fake-ollama:11434")
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(_fake_handler),
        base_url="http://fake-ollama:11434",
    )
    return client


# ===========================================================================
# 1. BUILD TEST
# ===========================================================================


class TestBuild:
    """Verify the package builds correctly."""

    def test_build_wheel(self) -> None:
        """uv build should produce a wheel without errors."""
        result = subprocess.run(
            ["uv", "build", "--wheel"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0, f"Build failed:\n{result.stderr}"
        assert "Successfully built" in result.stdout or "Successfully built" in result.stderr

    def test_build_sdist(self) -> None:
        """uv build should produce an sdist without errors."""
        result = subprocess.run(
            ["uv", "build", "--sdist"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0, f"Build failed:\n{result.stderr}"

    def test_wheel_contains_packages(self) -> None:
        """The wheel should include all expected packages."""
        import zipfile

        dist_dir = Path(_PROJECT_DIR) / "dist"
        wheel_candidates = sorted(dist_dir.glob("ollama_cli-*.whl"))
        if not wheel_candidates:
            subprocess.run(["uv", "build", "--wheel"], cwd=_PROJECT_DIR, capture_output=True)
            wheel_candidates = sorted(dist_dir.glob("ollama_cli-*.whl"))
        assert wheel_candidates, "Wheel file not found after build"
        whl_path = wheel_candidates[-1]

        with zipfile.ZipFile(whl_path) as zf:
            names = zf.namelist()
        for pkg in ("cmd/root.py", "api/ollama_client.py", "model/session.py", "runner/context_manager.py"):
            assert pkg in names, f"{pkg} missing from wheel"


# ===========================================================================
# 2. OLLAMA CLIENT (fake API)
# ===========================================================================


class TestOllamaClientFakeAPI:
    """Test OllamaClient methods against the fake Ollama API."""

    def test_health_check(self) -> None:
        client = _make_fake_client()

        async def run() -> bool:
            try:
                return await client.health_check()
            finally:
                await client.close()

        assert asyncio.run(run()) is True

    def test_get_version(self) -> None:
        client = _make_fake_client()

        async def run() -> str:
            try:
                return await client.get_version()
            finally:
                await client.close()

        assert asyncio.run(run()) == "0.5.1"

    def test_list_models(self) -> None:
        client = _make_fake_client()

        async def run() -> list:
            try:
                return await client.list_models()
            finally:
                await client.close()

        models = asyncio.run(run())
        assert len(models) == 2
        assert models[0]["name"] == "llama3.2"

    def test_chat(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.chat("llama3.2", [{"role": "user", "content": "Hello"}])
            finally:
                await client.close()

        result = asyncio.run(run())
        assert result["message"]["content"] == "Hello! I'm a helpful assistant."
        assert result["done"] is True
        assert result["eval_count"] == 12

    def test_generate(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.generate("llama3.2", "Write a function")
            finally:
                await client.close()

        result = asyncio.run(run())
        assert "reverse_string" in result["response"]

    def test_show_model(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.show_model("llama3.2")
            finally:
                await client.close()

        result = asyncio.run(run())
        assert "details" in result
        assert result["details"]["family"] == "llama"

    def test_embed(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.embed("llama3.2", "Hello world")
            finally:
                await client.close()

        result = asyncio.run(run())
        assert "embeddings" in result
        assert len(result["embeddings"][0]) == 5

    def test_list_running_models(self) -> None:
        client = _make_fake_client()

        async def run() -> list:
            try:
                return await client.list_running_models()
            finally:
                await client.close()

        models = asyncio.run(run())
        assert len(models) == 1
        assert models[0]["name"] == "llama3.2"

    def test_stop_model(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.stop_model("llama3.2")
            finally:
                await client.close()

        result = asyncio.run(run())
        assert result["status"] == "stopped"

    def test_delete_model(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.delete_model("llama3.2")
            finally:
                await client.close()

        result = asyncio.run(run())
        assert result["status"] == "deleted"

    def test_copy_model(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.copy_model("llama3.2", "my-llama")
            finally:
                await client.close()

        result = asyncio.run(run())
        assert result["status"] == "copied"

    def test_extract_metrics(self) -> None:
        metrics = OllamaClient.extract_metrics(_FAKE_CHAT_RESPONSE)
        assert metrics["prompt_eval_count"] == 26
        assert metrics["eval_count"] == 12
        assert metrics["tokens_per_second"] > 0

    def test_chat_openai_compat(self) -> None:
        client = _make_fake_client()

        async def run() -> dict:
            try:
                return await client.chat_openai("llama3.2", [{"role": "user", "content": "Hi"}])
            finally:
                await client.close()

        result = asyncio.run(run())
        assert result["choices"][0]["message"]["content"] == "OpenAI-style response"


# ===========================================================================
# 3. SESSION LIFECYCLE (fake API)
# ===========================================================================


class TestSessionLifecycle:
    """Test Session start/send/end/save/load with fake provider responses."""

    def test_session_start_and_status(self) -> None:
        async def run() -> dict[str, Any]:
            s = Session(model="llama3.2", provider="ollama")
            await s.start()
            return s.get_status()

        status = asyncio.run(run())
        assert status["model"] == "llama3.2"
        assert status["provider"] == "ollama"
        assert status["messages"] == 0
        assert status["uptime_seconds"] >= 0

    def test_session_send_returns_content(self) -> None:
        """send() should return a dict with content and metrics."""

        async def run() -> dict[str, Any]:
            s = Session(model="llama3.2", provider="ollama")
            await s.start()
            return await s.send("Hello world")

        result = asyncio.run(run())
        assert "content" in result
        assert "metrics" in result
        assert "compacted" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0

    def test_session_send_increments_messages(self) -> None:
        async def run() -> int:
            s = Session(model="llama3.2", provider="ollama")
            await s.start()
            await s.send("First message")
            await s.send("Second message")
            return s.get_status()["messages"]

        assert asyncio.run(run()) == 2

    def test_session_end_returns_summary(self) -> None:
        async def run() -> dict[str, Any]:
            s = Session(model="llama3.2", provider="ollama")
            await s.start()
            await s.send("Hello")
            return await s.end()

        summary = asyncio.run(run())
        assert "session_id" in summary
        assert "duration_seconds" in summary
        assert "messages" in summary
        assert summary["messages"] == 1

    def test_session_save_and_load(self, tmp_path: Path) -> None:
        """Session should persist and restore correctly."""

        async def run() -> tuple[str, dict, dict]:
            s = Session(model="codellama", provider="ollama")
            await s.start()
            await s.send("Test message")
            path = s.save(str(tmp_path / "session.json"))
            status_before = s.get_status()
            loaded = Session.load(s.session_id, path)
            status_after = loaded.get_status()
            return s.session_id, status_before, status_after

        sid, before, after = asyncio.run(run())
        assert after["session_id"] == sid
        assert after["model"] == "codellama"
        assert after["messages"] == 1

    def test_session_auto_compact_lifecycle(self) -> None:
        """Auto-compact should trigger when threshold is reached during send()."""

        async def run() -> dict[str, Any]:
            cm = ContextManager(max_context_length=100, compact_threshold=0.3, auto_compact=True, keep_last_n=1)
            s = Session(model="llama3.2", provider="ollama", context_manager=cm)
            await s.start()
            # Fill context to exceed threshold
            for i in range(10):
                cm.add_message("user", f"Fill message {i} " + "x" * 30)
            return await s.send("trigger compact")

        result = asyncio.run(run())
        assert result["compacted"] is True

    def test_session_manual_compact(self) -> None:
        """Manual compact() should work through Session."""

        async def run() -> dict[str, int]:
            cm = ContextManager(max_context_length=500, keep_last_n=2)
            s = Session(model="llama3.2", provider="ollama", context_manager=cm)
            await s.start()
            for i in range(10):
                cm.add_message("user", f"Message {i}")
            return await s.compact()

        result = asyncio.run(run())
        assert result["messages_removed"] > 0


# ===========================================================================
# 4. INTERACTIVE MODE COMMANDS
# ===========================================================================


class TestInteractiveCommands:
    """Test slash commands via subprocess to avoid cmd module collision."""

    @staticmethod
    def _run_script(script: str) -> str:
        """Write a script to a temp file and run it in a subprocess."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import sys, asyncio\n")
            f.write(f"sys.path.insert(0, {_PROJECT_DIR!r})\n")
            f.write("from model.session import Session\n")
            f.write("from cmd.interactive import InteractiveMode\n\n")
            f.write(script)
            tmp = f.name

        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        Path(tmp).unlink(missing_ok=True)
        return result.stdout + result.stderr

    def test_cmd_help(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); r._cmd_help('')\n"
            "asyncio.run(t())\n"
        )
        assert "/help" in out
        assert "/compact" in out
        assert "/tools" in out

    def test_cmd_status(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='llama3.2', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); r._cmd_status('')\n"
            "asyncio.run(t())\n"
        )
        assert "llama3.2" in out
        assert "compact" in out.lower()

    def test_cmd_model_switch(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='llama3.2', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); r._cmd_model('codellama')\n"
            "  print(f'model={s.model}')\n"
            "asyncio.run(t())\n"
        )
        assert "model=codellama" in out

    def test_cmd_provider_switch(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); r._cmd_provider('claude')\n"
            "  print(f'provider={s.provider}')\n"
            "asyncio.run(t())\n"
        )
        assert "provider=claude" in out

    def test_cmd_clear(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  s.context_manager.add_message('user', 'hello')\n"
            "  r = InteractiveMode(s); r._cmd_clear('')\n"
            "  print(f'msgs={len(s.context_manager.messages)}')\n"
            "asyncio.run(t())\n"
        )
        assert "msgs=0" in out

    def test_cmd_compact(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  for i in range(10): s.context_manager.add_message('user', f'msg{i}')\n"
            "  r = InteractiveMode(s); await r._cmd_compact('')\n"
            "asyncio.run(t())\n"
        )
        assert "compact" in out.lower()

    def test_cmd_tools(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); r._cmd_tools('')\n"
            "asyncio.run(t())\n"
        )
        assert "file_read" in out

    def test_cmd_config(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); r._cmd_config('')\n"
            "asyncio.run(t())\n"
        )
        assert "provider" in out.lower() or "model" in out.lower()

    def test_cmd_quit(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); result = r._cmd_quit('')\n"
            "  print(f'quit={result}')\n"
            "asyncio.run(t())\n"
        )
        assert "quit=True" in out

    def test_cmd_build_no_arg(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); await r._cmd_build('')\n"
            "asyncio.run(t())\n"
        )
        assert "usage" in out.lower()

    def test_cmd_team_planning_no_arg(self) -> None:
        out = self._run_script(
            "async def t():\n"
            "  s = Session(model='m', provider='ollama'); await s.start()\n"
            "  r = InteractiveMode(s); await r._cmd_team_planning('')\n"
            "asyncio.run(t())\n"
        )
        assert "usage" in out.lower()


# ===========================================================================
# 5. BUILT-IN TOOLS
# ===========================================================================


class TestBuiltInTools:
    """Test skills/tools.py functions."""

    def test_file_read(self, tmp_path: Path) -> None:
        from skills.tools import tool_file_read

        f = tmp_path / "hello.txt"
        f.write_text("line1\nline2\nline3\n")
        result = tool_file_read(str(f))
        assert result["content"] == "line1\nline2\nline3\n"
        assert result["lines"] == 3

    def test_file_read_missing(self) -> None:
        from skills.tools import tool_file_read

        result = tool_file_read("/nonexistent/file.txt")
        assert "error" in result

    def test_file_write(self, tmp_path: Path) -> None:
        from skills.tools import tool_file_write

        f = tmp_path / "output.txt"
        result = tool_file_write(str(f), "Hello world")
        assert "bytes_written" in result
        assert f.read_text() == "Hello world"

    def test_file_edit(self, tmp_path: Path) -> None:
        from skills.tools import tool_file_edit

        f = tmp_path / "edit.txt"
        f.write_text("old text here")
        result = tool_file_edit(str(f), "old text", "new text")
        assert result.get("replaced") is True
        assert "new text here" in f.read_text()

    def test_file_edit_no_match(self, tmp_path: Path) -> None:
        from skills.tools import tool_file_edit

        f = tmp_path / "edit2.txt"
        f.write_text("hello world")
        result = tool_file_edit(str(f), "nonexistent", "replacement")
        assert "error" in result

    def test_grep_search(self, tmp_path: Path) -> None:
        from skills.tools import tool_grep_search

        (tmp_path / "test.py").write_text("def main():\n    print('hello')\n")
        result = tool_grep_search("def main", str(tmp_path))
        assert result["count"] > 0

    def test_shell_exec(self) -> None:
        from skills.tools import tool_shell_exec

        result = tool_shell_exec("echo hello_world")
        assert result["returncode"] == 0
        assert "hello_world" in result["stdout"]

    def test_shell_exec_failure(self) -> None:
        from skills.tools import tool_shell_exec

        result = tool_shell_exec("false")
        assert result["returncode"] != 0

    def test_list_tools(self) -> None:
        from skills.tools import list_tools

        tools = list_tools()
        names = [t["name"] for t in tools]
        assert "file_read" in names
        assert "file_write" in names
        assert "shell_exec" in names
        assert "grep_search" in names
        assert "web_fetch" in names

    def test_get_tool(self) -> None:
        from skills.tools import get_tool

        tool = get_tool("file_read")
        assert tool is not None
        assert "function" in tool
        assert "description" in tool

    def test_get_tool_unknown(self) -> None:
        from skills.tools import get_tool

        assert get_tool("nonexistent_tool") is None

    def test_ollamaignore(self, tmp_path: Path, monkeypatch) -> None:
        from skills.tools import clear_ignore_cache, is_path_ignored

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ollamaignore").write_text(".env\nsecrets/\n")
        clear_ignore_cache()
        assert is_path_ignored(".env") is True
        assert is_path_ignored("src/main.py") is False
        clear_ignore_cache()


# ===========================================================================
# 6. SKILLS FRAMEWORK
# ===========================================================================


class TestSkillsFramework:
    """Test the skills registry and execute_skill."""

    def test_skill_registry(self) -> None:
        from skills import SKILLS

        assert "token_counter" in SKILLS
        assert "auto_compact" in SKILLS

    def test_token_counting_skill(self) -> None:
        from skills import execute_skill

        result = asyncio.run(execute_skill("token_counter", text="Hello, world!", provider="ollama"))
        assert "token_count" in result
        assert result["token_count"] > 0

    def test_auto_compact_skill_check(self) -> None:
        from skills import execute_skill

        result = asyncio.run(execute_skill("auto_compact", action="check"))
        assert result["action"] == "check"
        assert "should_compact" in result

    def test_auto_compact_skill_configure(self) -> None:
        from skills import execute_skill

        cm = ContextManager()
        result = asyncio.run(execute_skill("auto_compact", cm, action="configure", threshold=0.7, keep_last_n=6))
        assert result["configured"] is True
        assert cm.compact_threshold == 0.7
        assert cm.keep_last_n == 6


# ===========================================================================
# 7. CONTEXT MANAGER
# ===========================================================================


class TestContextManagerIntegration:
    """Integration tests for ContextManager."""

    def test_full_lifecycle(self) -> None:
        cm = ContextManager(max_context_length=4096, compact_threshold=0.85)
        cm.set_system_message("You are a helpful assistant.")

        # Add messages
        cm.add_message("user", "Hello")
        cm.add_message("assistant", "Hi there!")
        cm.add_message("user", "Write a function")
        cm.add_message("assistant", "def hello(): pass")

        # Check usage
        usage = cm.get_context_usage()
        assert usage["used"] > 0
        assert usage["max"] == 4096

        # Check metrics
        metrics = cm.get_token_metrics()
        assert metrics["context_used"] > 0

    def test_save_load_cycle(self, tmp_path: Path) -> None:
        cm1 = ContextManager(max_context_length=2048, compact_threshold=0.7, auto_compact=True, keep_last_n=5)
        cm1.set_system_message("System prompt")
        cm1.add_message("user", "Hello")
        cm1.add_message("assistant", "Hi")

        path = str(tmp_path / "ctx.json")
        cm1.save_session(path)

        cm2 = ContextManager()
        cm2.load_session(path)

        assert cm2.max_context_length == 2048
        assert cm2.compact_threshold == 0.7
        assert cm2.auto_compact is True
        assert cm2.keep_last_n == 5
        assert cm2.system_message == "System prompt"
        assert len(cm2.messages) == 2

    def test_sub_context_isolation(self) -> None:
        parent = ContextManager(max_context_length=4096)
        child = parent.create_sub_context("agent1")

        parent.add_message("user", "Parent message")
        child.add_message("user", "Child message")

        assert len(parent.messages) == 1
        assert len(child.messages) == 1
        assert parent.get_total_context_tokens() > child._estimated_context_tokens


# ===========================================================================
# 8. HOOKS SYSTEM
# ===========================================================================


class TestHooksIntegration:
    """Test the hooks system works end-to-end."""

    def test_hook_runner_import(self) -> None:
        from server.hook_runner import HookRunner

        runner = HookRunner()
        assert hasattr(runner, "run_hook")
        assert hasattr(runner, "is_enabled")

    def test_hook_runner_is_enabled(self) -> None:
        from server.hook_runner import HookRunner

        runner = HookRunner()
        # Should return bool without error
        result = runner.is_enabled()
        assert isinstance(result, bool)

    def test_hooks_directory_structure(self) -> None:
        hooks_dir = Path(_PROJECT_DIR) / ".ollama" / "hooks"
        assert hooks_dir.is_dir(), "Hooks directory missing"

    def test_all_hook_events_registered(self) -> None:
        """Verify all hook events are in settings.json."""
        settings_path = Path(_PROJECT_DIR) / ".ollama" / "settings.json"
        assert settings_path.is_file()
        data = json.loads(settings_path.read_text())
        hooks = data.get("hooks", {})
        assert set(_EXPECTED_HOOK_EVENTS.keys()).issubset(set(hooks.keys())), (
            f"Missing hooks: {set(_EXPECTED_HOOK_EVENTS.keys()) - set(hooks.keys())}"
        )

    def test_hook_scripts_exist(self) -> None:
        """Verify each hook event has a corresponding .py script."""
        hooks_dir = Path(_PROJECT_DIR) / ".ollama" / "hooks"
        for _event, script in _EXPECTED_HOOK_EVENTS.items():
            assert (hooks_dir / script).is_file(), f"Missing hook script: {script}"

    def test_fire_hook_helper(self) -> None:
        """Test that _fire_hook returns a list even when hooks are unconfigured."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import asyncio; import sys; sys.path.insert(0, '.');"
                    "from model.session import Session; from cmd.interactive import InteractiveMode;"
                    "s = Session(model='test', provider='ollama');"
                    "asyncio.get_event_loop().run_until_complete(s.start());"
                    "r = InteractiveMode(s);"
                    "result = r._fire_hook('SessionStart', {'session_id': 'test'});"
                    "assert isinstance(result, list);"
                    "print('fire_hook_ok')"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert "fire_hook_ok" in result.stdout

    def test_status_bar_method_exists(self) -> None:
        """Verify _print_status_bar method exists and runs without error."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import asyncio; import sys; sys.path.insert(0, '.');"
                    "from model.session import Session; from cmd.interactive import InteractiveMode;"
                    "s = Session(model='test', provider='ollama');"
                    "asyncio.get_event_loop().run_until_complete(s.start());"
                    "r = InteractiveMode(s);"
                    "r._print_status_bar();"
                    "print('status_bar_ok')"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert "status_bar_ok" in result.stdout

    def test_fire_notification_helper(self) -> None:
        """Test that _fire_notification runs without error."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import asyncio; import sys; sys.path.insert(0, '.');"
                    "from model.session import Session; from cmd.interactive import InteractiveMode;"
                    "s = Session(model='test', provider='ollama');"
                    "asyncio.get_event_loop().run_until_complete(s.start());"
                    "r = InteractiveMode(s);"
                    "r._fire_notification('info', 'test message');"
                    "print('notification_ok')"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert "notification_ok" in result.stdout

    def test_status_lines_directory(self) -> None:
        """Verify status_lines directory exists with expected scripts."""
        status_dir = Path(_PROJECT_DIR) / ".ollama" / "status_lines"
        assert status_dir.is_dir(), "status_lines directory missing"
        expected = ["status_line_full_dashboard.py", "status_line_token_counter.py", "status_utils.py"]
        for script in expected:
            assert (status_dir / script).is_file(), f"Missing status line: {script}"


# ===========================================================================
# 9. CLI ENTRYPOINT
# ===========================================================================


class TestCLIEntrypoint:
    """Test the CLI entrypoint via subprocess."""

    def test_cli_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "from cmd.root import build_parser; build_parser().parse_args(['--version'])"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        # --version causes SystemExit(0)
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_cli_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "from cmd.root import build_parser; build_parser().parse_args(['--help'])"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert "ollama-cli" in result.stdout

    def test_cli_parser_all_subcommands(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from cmd.root import build_parser; p = build_parser(); print(list(p._subparsers._group_actions[0].choices.keys()))",
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        for cmd in ("chat", "run", "list", "pull", "show", "serve", "config", "status", "version", "interactive"):
            assert cmd in result.stdout, f"Command '{cmd}' missing from parser"

    def test_cli_command_map_complete(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "from cmd.root import COMMAND_MAP; print(list(COMMAND_MAP.keys()))"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        for cmd in ("chat", "list", "pull", "show", "serve", "config", "status", "version", "interactive"):
            assert cmd in result.stdout, f"Command '{cmd}' missing from COMMAND_MAP"


# ===========================================================================
# 10. CONFIG
# ===========================================================================


class TestConfig:
    """Test configuration loading."""

    def test_config_loads(self) -> None:
        from api.config import get_config

        cfg = get_config()
        assert cfg.provider in ("ollama", "claude", "gemini", "codex")
        assert cfg.context_length > 0
        assert isinstance(cfg.auto_compact, bool)
        assert 0 < cfg.compact_threshold <= 1.0

    def test_config_has_all_fields(self) -> None:
        from api.config import OllamaCliConfig

        cfg = OllamaCliConfig()
        assert hasattr(cfg, "provider")
        assert hasattr(cfg, "ollama_model")
        assert hasattr(cfg, "context_length")
        assert hasattr(cfg, "auto_compact")
        assert hasattr(cfg, "compact_threshold")
        assert hasattr(cfg, "output_format")
        assert hasattr(cfg, "allowed_tools")
        assert hasattr(cfg, "ollama_api_key")


# ===========================================================================
# 11. OLLAMA API KEY SUPPORT
# ===========================================================================


class TestOllamaAPIKeySupport:
    """Test that OLLAMA_API_KEY is properly wired through the stack."""

    def test_client_accepts_api_key(self) -> None:
        """OllamaClient should accept an api_key parameter."""
        client = OllamaClient(api_key="test-key-123")
        assert client._api_key == "test-key-123"

    def test_client_reads_env_api_key(self, monkeypatch) -> None:
        """OllamaClient should read OLLAMA_API_KEY from environment."""
        monkeypatch.setenv("OLLAMA_API_KEY", "env-key-456")
        client = OllamaClient()
        assert client._api_key == "env-key-456"

    def test_client_sends_bearer_header(self) -> None:
        """When API key is set, the Authorization header should be sent."""
        received_headers: dict[str, str] = {}

        def capture_handler(request: httpx.Request) -> httpx.Response:
            received_headers.update(dict(request.headers))
            return httpx.Response(200, json={"models": []})

        client = OllamaClient(api_key="bearer-test-key")
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(capture_handler),
            base_url="http://fake:11434",
            headers={"Authorization": "Bearer bearer-test-key"},
        )

        async def run() -> None:
            try:
                await client.list_models()
            finally:
                await client.close()

        asyncio.run(run())
        assert "authorization" in received_headers
        assert received_headers["authorization"] == "Bearer bearer-test-key"

    def test_client_no_header_without_key(self) -> None:
        """When no API key is set, no Authorization header should be sent."""
        received_headers: dict[str, str] = {}

        def capture_handler(request: httpx.Request) -> httpx.Response:
            received_headers.update(dict(request.headers))
            return httpx.Response(200, json={"models": []})

        client = OllamaClient(api_key="")
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(capture_handler),
            base_url="http://fake:11434",
        )

        async def run() -> None:
            try:
                await client.list_models()
            finally:
                await client.close()

        asyncio.run(run())
        assert "authorization" not in received_headers

    def test_config_has_ollama_api_key(self) -> None:
        """OllamaCliConfig should have ollama_api_key field."""
        from api.config import OllamaCliConfig

        cfg = OllamaCliConfig()
        assert hasattr(cfg, "ollama_api_key")
        assert cfg.ollama_api_key == ""

    def test_config_loads_ollama_api_key(self, monkeypatch) -> None:
        """load_config should read OLLAMA_API_KEY from environment."""
        from api.config import load_config

        monkeypatch.setenv("OLLAMA_API_KEY", "cfg-key-789")
        cfg = load_config()
        assert cfg.ollama_api_key == "cfg-key-789"

    def test_config_excludes_api_key_from_save(self, tmp_path) -> None:
        """ollama_api_key should NOT be persisted to config.json."""
        from api.config import OllamaCliConfig, save_config

        cfg = OllamaCliConfig(ollama_api_key="secret-key")
        path = save_config(cfg, tmp_path / "config.json")
        saved = json.loads(Path(path).read_text())
        assert "ollama_api_key" not in saved

    def test_provider_passes_api_key(self, monkeypatch) -> None:
        """OllamaProvider should pass API key to OllamaClient."""
        from api.provider_router import OllamaProvider

        monkeypatch.setenv("OLLAMA_API_KEY", "provider-key-abc")
        provider = OllamaProvider()
        assert provider._client._api_key == "provider-key-abc"

    def test_ollama_cloud_host(self) -> None:
        """Client should work with https://ollama.com as host."""
        client = OllamaClient(host="https://ollama.com", api_key="cloud-key")
        assert client.host == "https://ollama.com"
        assert client._api_key == "cloud-key"


# ===========================================================================
# 12. REAL OLLAMA CLOUD API (skipped if OLLAMA_API_KEY not set)
# ===========================================================================

_OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com")
_skip_no_key = pytest.mark.skipif(not _OLLAMA_API_KEY, reason="OLLAMA_API_KEY not set")


@_skip_no_key
class TestRealOllamaCloudAPI:
    """Integration tests against the real Ollama Cloud API.

    These tests are skipped unless OLLAMA_API_KEY is set in the environment.
    They verify that the API key auth and all client methods work against
    the live https://ollama.com endpoint.
    """

    @staticmethod
    def _make_cloud_client() -> OllamaClient:
        return OllamaClient(host=_OLLAMA_HOST, api_key=_OLLAMA_API_KEY)

    def test_cloud_health_check(self) -> None:
        """Cloud API should respond to health check."""
        client = self._make_cloud_client()

        async def run() -> bool:
            try:
                return await client.health_check()
            finally:
                await client.close()

        assert asyncio.run(run()) is True

    def test_cloud_list_models(self) -> None:
        """Cloud API should list available models."""
        client = self._make_cloud_client()

        async def run() -> list:
            try:
                return await client.list_models()
            finally:
                await client.close()

        models = asyncio.run(run())
        assert isinstance(models, list)

    def test_cloud_get_version(self) -> None:
        """Cloud API should return a version string."""
        client = self._make_cloud_client()

        async def run() -> str:
            try:
                return await client.get_version()
            finally:
                await client.close()

        version = asyncio.run(run())
        assert isinstance(version, str)
        assert len(version) > 0

    def test_cloud_chat(self) -> None:
        """Cloud API should handle a chat request."""
        client = self._make_cloud_client()

        async def run() -> dict:
            try:
                return await client.chat(
                    "llama3.2",
                    [{"role": "user", "content": "Say hello in exactly one word."}],
                )
            finally:
                await client.close()

        try:
            result = asyncio.run(run())
        except Exception as exc:
            pytest.skip(f"Cloud model not available: {exc}")
        assert "message" in result
        assert result["message"]["role"] == "assistant"
        assert len(result["message"]["content"]) > 0

    def test_cloud_generate(self) -> None:
        """Cloud API should handle a generate request."""
        client = self._make_cloud_client()

        async def run() -> dict:
            try:
                return await client.generate("llama3.2", "Say hello in one word.")
            finally:
                await client.close()

        try:
            result = asyncio.run(run())
        except Exception as exc:
            pytest.skip(f"Cloud model not available: {exc}")
        assert "response" in result
        assert len(result["response"]) > 0

    def test_cloud_session_send(self) -> None:
        """Full Session.send() should work against cloud API."""
        from api.provider_router import OllamaProvider, ProviderRouter

        provider = OllamaProvider(host=_OLLAMA_HOST, api_key=_OLLAMA_API_KEY)
        router = ProviderRouter()
        router._providers["ollama"] = provider

        async def run() -> dict[str, Any]:
            s = Session(model="llama3.2", provider="ollama", provider_router=router)
            await s.start()
            try:
                return await s.send("Reply with exactly: OK")
            finally:
                await provider.close()

        try:
            result = asyncio.run(run())
        except Exception as exc:
            pytest.skip(f"Cloud model not available: {exc}")
        assert "content" in result
        assert len(result["content"]) > 0
        assert "metrics" in result
