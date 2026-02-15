"""Tests for features inspired by Gemini CLI, Claude Code, and OpenAI Codex.

Covers:
- Built-in tools (skills/tools.py): file_read, file_write, file_edit, grep_search,
  shell_exec, web_fetch, .qarinignore support
- New CLI flags: --allowed-tools, --output-format
- New slash commands registered in InteractiveMode: /memory, /tools, /tool,
  /diff, /config, /bug
- Hook integration with tool execution
"""

import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# skills/tools.py tests
# ---------------------------------------------------------------------------


class TestToolFileRead:
    """Tests for the file_read tool."""

    def test_read_existing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "hello.txt"
        f.write_text("line1\nline2\nline3\n")
        from skills.tools import tool_file_read

        result = tool_file_read(str(f))
        assert "error" not in result
        assert result["lines"] == 3
        assert "line1" in result["content"]

    def test_read_missing_file(self) -> None:
        from skills.tools import tool_file_read

        result = tool_file_read("/nonexistent/path/abc.txt")
        assert "error" in result

    def test_read_respects_max_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "big.txt"
        f.write_text("\n".join(f"line{i}" for i in range(1000)))
        from skills.tools import tool_file_read

        result = tool_file_read(str(f), max_lines=10)
        assert "more lines" in result["content"]


class TestToolFileWrite:
    """Tests for the file_write tool."""

    def test_write_new_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"
        from skills.tools import tool_file_write

        result = tool_file_write(str(target), "hello world")
        assert "error" not in result
        assert target.read_text() == "hello world"

    def test_write_creates_parents(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c.txt"
        from skills.tools import tool_file_write

        result = tool_file_write(str(target), "nested")
        assert "error" not in result
        assert target.read_text() == "nested"


class TestToolFileEdit:
    """Tests for the file_edit tool."""

    def test_edit_replaces_text(self, tmp_path: Path) -> None:
        f = tmp_path / "code.py"
        f.write_text("x = 1\ny = 2\n")
        from skills.tools import tool_file_edit

        result = tool_file_edit(str(f), "x = 1", "x = 42")
        assert result.get("replaced") is True
        assert "x = 42" in f.read_text()

    def test_edit_missing_text(self, tmp_path: Path) -> None:
        f = tmp_path / "code.py"
        f.write_text("x = 1\n")
        from skills.tools import tool_file_edit

        result = tool_file_edit(str(f), "NOT_HERE", "replacement")
        assert "error" in result


class TestToolGrepSearch:
    """Tests for the grep_search tool."""

    def test_grep_finds_pattern(self, tmp_path: Path) -> None:
        f = tmp_path / "data.py"
        f.write_text("def hello():\n    pass\n")
        from skills.tools import tool_grep_search

        result = tool_grep_search("def hello", str(tmp_path))
        assert "error" not in result
        assert result["count"] >= 1

    def test_grep_no_match(self, tmp_path: Path) -> None:
        f = tmp_path / "data.py"
        f.write_text("x = 1\n")
        from skills.tools import tool_grep_search

        result = tool_grep_search("ZZZZNOTFOUND", str(tmp_path))
        assert result["count"] == 0


class TestToolShellExec:
    """Tests for the shell_exec tool."""

    def test_echo_command(self) -> None:
        from skills.tools import tool_shell_exec

        result = tool_shell_exec("echo hello")
        assert "error" not in result
        assert "hello" in result["stdout"]

    def test_failing_command(self) -> None:
        from skills.tools import tool_shell_exec

        result = tool_shell_exec("exit 1")
        assert result["returncode"] == 1


class TestToolRegistry:
    """Tests for the tool registry functions."""

    def test_list_tools_returns_all(self) -> None:
        from skills.tools import list_tools

        tools = list_tools()
        names = [t["name"] for t in tools]
        assert "file_read" in names
        assert "file_write" in names
        assert "shell_exec" in names
        assert "web_fetch" in names

    def test_get_tool_known(self) -> None:
        from skills.tools import get_tool

        entry = get_tool("file_read")
        assert entry is not None
        assert callable(entry["function"])

    def test_get_tool_unknown(self) -> None:
        from skills.tools import get_tool

        assert get_tool("nonexistent_tool") is None


class TestOllamaIgnore:
    """Tests for .qarinignore support."""

    def test_ignored_path(self, tmp_path: Path, monkeypatch) -> None:
        ignore_file = tmp_path / ".qarinignore"
        ignore_file.write_text("secret.txt\n*.key\n")
        monkeypatch.chdir(tmp_path)

        from skills.tools import clear_ignore_cache, is_path_ignored

        clear_ignore_cache()

        assert is_path_ignored("secret.txt") is True
        assert is_path_ignored("my.key") is True
        assert is_path_ignored("readme.md") is False

        clear_ignore_cache()

    def test_file_read_blocked_by_ignore(self, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / ".qarinignore").write_text("blocked.txt\n")
        (tmp_path / "blocked.txt").write_text("secret data")
        monkeypatch.chdir(tmp_path)

        from skills.tools import clear_ignore_cache, tool_file_read

        clear_ignore_cache()

        result = tool_file_read("blocked.txt")
        assert "error" in result
        assert "ignored" in result["error"].lower()

        clear_ignore_cache()


# ---------------------------------------------------------------------------
# CLI flag tests (--allowed-tools, --output-format)
# ---------------------------------------------------------------------------

_PROJECT_DIR = str(Path(__file__).parent.parent)


def test_allowed_tools_flag_parsed() -> None:
    """--allowed-tools should be parsed into args."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from qarin_cmd.root import build_parser; "
                "a = build_parser().parse_args(['--allowed-tools', 'file_read,grep_search', 'version']); "
                "print(a.allowed_tools)"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert "file_read,grep_search" in result.stdout


def test_output_format_flag_parsed() -> None:
    """--output-format should be parsed into args."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from qarin_cmd.root import build_parser; "
                "a = build_parser().parse_args(['--output-format', 'json', 'version']); "
                "print(a.output_format)"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert result.stdout.strip() == "json"


def test_output_format_choices() -> None:
    """--output-format should only accept text/json/markdown."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from qarin_cmd.root import build_parser; build_parser().parse_args(['--output-format', 'xml'])",
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert result.returncode != 0


def test_help_includes_allowed_tools() -> None:
    """--help should mention --allowed-tools."""
    result = subprocess.run(
        [sys.executable, "-c", "from qarin_cmd.root import build_parser; build_parser().parse_args(['--help'])"],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert "--allowed-tools" in result.stdout


def test_help_includes_output_format() -> None:
    """--help should mention --output-format."""
    result = subprocess.run(
        [sys.executable, "-c", "from qarin_cmd.root import build_parser; build_parser().parse_args(['--help'])"],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert "--output-format" in result.stdout


# ---------------------------------------------------------------------------
# New slash command registration tests
# ---------------------------------------------------------------------------


def test_interactive_mode_has_new_commands() -> None:
    """InteractiveMode._COMMAND_TABLE must include new commands."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from qarin_cmd.interactive import InteractiveMode; "
                "cmds = list(InteractiveMode._COMMAND_TABLE.keys()); "
                "print(','.join(cmds))"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    out = result.stdout.strip()
    for cmd in (
        "/memory",
        "/tools",
        "/tool",
        "/diff",
        "/config",
        "/bug",
        "/team_planning",
        "/build",
        "/resume",
        "/update_status_line",
    ):
        assert cmd in out, f"{cmd} missing from InteractiveMode._COMMAND_TABLE"


def test_interactive_help_mentions_new_commands() -> None:
    """The /help handler should mention new commands."""
    script = (
        "import sys, asyncio\n"
        "sys.path.insert(0, '.')\n"
        "from model.session import Session\n"
        "from qarin_cmd.interactive import InteractiveMode\n"
        "async def t():\n"
        "    s = Session(model='m', provider='ollama')\n"
        "    await s.start()\n"
        "    r = InteractiveMode(s)\n"
        "    r._cmd_help('')\n"
        "asyncio.run(t())\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    for keyword in (
        "/memory",
        "/tools",
        "/tool",
        "/diff",
        "/config",
        "/bug",
        "/team_planning",
        "/build",
        "/resume",
        "/update_status_line",
    ):
        assert keyword in result.stdout, f"{keyword} missing from /help output"


# ---------------------------------------------------------------------------
# Hook integration test
# ---------------------------------------------------------------------------


def test_hook_runner_loads_settings() -> None:
    """HookRunner should load settings.json without error."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            ("from server.hook_runner import HookRunner; r = HookRunner(); print('enabled:', r.is_enabled())"),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert result.returncode == 0
    assert "enabled:" in result.stdout


def test_skills_framework_still_works() -> None:
    """The skills registry must still list all expected skills."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            ("from skills import SKILLS; print(','.join(sorted(SKILLS.keys())))"),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert result.returncode == 0
    for skill in ("token_counter", "auto_compact"):
        assert skill in result.stdout


# ---------------------------------------------------------------------------
# New orchestration command tests (/team_planning, /build, /resume,
# /update_status_line)
# ---------------------------------------------------------------------------


class TestResumeCommand:
    """Tests for the /resume slash command."""

    def test_resume_no_tasks(self, tmp_path: Path, monkeypatch) -> None:
        """When no tasks exist, /resume should print a message."""
        monkeypatch.chdir(tmp_path)
        script = (
            "import sys, asyncio\n"
            "sys.path.insert(0, '.')\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    r = InteractiveMode(s)\n"
            "    r._cmd_resume('')\n"
            "asyncio.run(t())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "No previous tasks" in result.stdout

    def test_resume_lists_tasks(self, tmp_path: Path, monkeypatch) -> None:
        """When tasks exist, /resume should list them."""
        monkeypatch.chdir(tmp_path)
        tasks_dir = tmp_path / ".qarin" / "tasks"
        tasks_dir.mkdir(parents=True)
        import json

        task = {
            "id": "test-task",
            "type": "team_planning",
            "description": "Test task",
            "status": "planned",
        }
        (tasks_dir / "test-task.json").write_text(json.dumps(task))

        script = (
            "import sys, asyncio\n"
            "sys.path.insert(0, PROJ)\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    r = InteractiveMode(s)\n"
            "    r._cmd_resume('')\n"
            "asyncio.run(t())\n"
        ).replace("PROJ", repr(_PROJECT_DIR))

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert "test-task" in result.stdout


class TestUpdateStatusLine:
    """Tests for the /update_status_line slash command."""

    def test_update_creates_extras(self, tmp_path: Path, monkeypatch) -> None:
        """Should write key-value pair to session file."""
        monkeypatch.chdir(tmp_path)

        session_dir = tmp_path / ".qarin" / "sessions"
        session_dir.mkdir(parents=True)

        # The /update_status_line command requires an existing session file.
        # The script saves the session first (creating the file), then updates.
        script = (
            "import sys, asyncio\n"
            "sys.path.insert(0, PROJ)\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    s.save()\n"
            "    r = InteractiveMode(s)\n"
            "    r._cmd_update_status_line('project myapp')\n"
            "asyncio.run(t())\n"
        ).replace("PROJ", repr(_PROJECT_DIR))

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0
        assert "project" in result.stdout.lower()

    def test_update_missing_value(self) -> None:
        """Should error when only key is provided."""
        script = (
            "import sys, asyncio\n"
            "sys.path.insert(0, '.')\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    r = InteractiveMode(s)\n"
            "    r._cmd_update_status_line('onlykey')\n"
            "asyncio.run(t())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "required" in result.stdout.lower()


class TestBuildCommand:
    """Tests for the /build slash command."""

    def test_build_missing_plan(self) -> None:
        """Should error when plan path is not given."""
        script = (
            "import sys, asyncio\n"
            "sys.path.insert(0, '.')\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    r = InteractiveMode(s)\n"
            "    result = await r._cmd_build('')\n"
            "    print('exit:', result)\n"
            "asyncio.run(t())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "Usage" in result.stdout

    def test_build_nonexistent_plan(self) -> None:
        """Should error when plan file does not exist."""
        script = (
            "import sys, asyncio\n"
            "sys.path.insert(0, '.')\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    r = InteractiveMode(s)\n"
            "    result = await r._cmd_build('/nonexistent/plan.md')\n"
            "    print('exit:', result)\n"
            "asyncio.run(t())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "not found" in result.stdout.lower()

    def test_build_with_plan_file(self) -> None:
        """Should run without AttributeError when building a real plan file."""
        script = (
            "import sys, asyncio, tempfile, os\n"
            "sys.path.insert(0, '.')\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    # Pre-send a message so the planner_messages path is exercised\n"
            "    s.agent_comm.send(sender_id='planner', recipient_id='builder',\n"
            "                      content='context info', message_type='info')\n"
            "    r = InteractiveMode(s)\n"
            "    fd, p = tempfile.mkstemp(suffix='.md')\n"
            "    try:\n"
            "        with open(p, 'w') as f:\n"
            "            f.write('# Plan\\nStep 1: test\\n')\n"
            "        result = await r._cmd_build(p)\n"
            "        print('exit:', result)\n"
            "    finally:\n"
            "        os.unlink(p)\n"
            "asyncio.run(t())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "AttributeError" not in result.stderr


class TestTeamPlanningCommand:
    """Tests for the /team_planning slash command."""

    def test_team_planning_no_arg(self) -> None:
        """Should show usage when no argument is given."""
        script = (
            "import sys, asyncio\n"
            "sys.path.insert(0, '.')\n"
            "from model.session import Session\n"
            "from qarin_cmd.interactive import InteractiveMode\n"
            "async def t():\n"
            "    s = Session(model='m', provider='ollama')\n"
            "    await s.start()\n"
            "    r = InteractiveMode(s)\n"
            "    result = await r._cmd_team_planning('')\n"
            "    print('exit:', result)\n"
            "asyncio.run(t())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "Usage" in result.stdout
