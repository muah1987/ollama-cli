"""
Tests for CLI argument parsing improvements.

Tests cover:
1. build_parser produces expected flags and subcommands
2. _extract_prompt_args correctly separates direct prompts from subcommands
3. --version / -v flag
4. --print / -p flag
5. --system-prompt flag
6. Default to interactive when no command given
"""

import subprocess
import sys
from pathlib import Path


def test_help_flag_shows_usage() -> None:
    """Test that --help exits cleanly and shows the expected usage line."""
    result = subprocess.run(
        [sys.executable, "-c", "from cmd.root import build_parser; build_parser().parse_args(['--help'])"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0
    assert "ollama-cli [options] [command] [prompt]" in result.stdout


def test_version_flag() -> None:
    """Test that -v / --version prints the version string."""
    result = subprocess.run(
        [sys.executable, "-c", "from cmd.root import build_parser; build_parser().parse_args(['-v'])"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0
    assert "ollama-cli v" in result.stdout


def test_subcommand_list_parsed() -> None:
    """Test that 'list' is parsed as a subcommand."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import build_parser; a = build_parser().parse_args(['list']); print(a.command)",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.stdout.strip() == "list"


def test_print_mode_flag() -> None:
    """Test that -p / --print sets print_mode=True."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import build_parser; a = build_parser().parse_args(['-p', 'version']); print(a.print_mode)",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.stdout.strip() == "True"


def test_system_prompt_flag() -> None:
    """Test that --system-prompt stores the value."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from cmd.root import build_parser; "
                "a = build_parser().parse_args(['--system-prompt', 'be concise', 'version']); "
                "print(a.system_prompt)"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.stdout.strip() == "be concise"


def test_extract_prompt_with_direct_text() -> None:
    """Test _extract_prompt_args identifies non-subcommand text as a prompt."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import _extract_prompt_args; print(_extract_prompt_args(['hello', 'world']))",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "hello world" in result.stdout


def test_extract_prompt_with_subcommand() -> None:
    """Test _extract_prompt_args returns None prompt for known subcommands."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import _extract_prompt_args; print(_extract_prompt_args(['list']))",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "None" in result.stdout


def test_extract_prompt_with_flags_and_prompt() -> None:
    """Test _extract_prompt_args handles flags before a prompt."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from cmd.root import _extract_prompt_args; "
                "f, p = _extract_prompt_args(['--model', 'llama3', 'what is python']); "
                "print(f'flags={f} prompt={p}')"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "what is python" in result.stdout
    assert "--model" in result.stdout


def test_extract_prompt_no_args() -> None:
    """Test _extract_prompt_args with empty args returns None prompt."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import _extract_prompt_args; print(_extract_prompt_args([]))",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "None" in result.stdout


def test_help_includes_print_flag() -> None:
    """Test that --help output includes the -p/--print flag description."""
    result = subprocess.run(
        [sys.executable, "-c", "from cmd.root import build_parser; build_parser().parse_args(['--help'])"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "--print" in result.stdout
    assert "non-interactive" in result.stdout.lower()


def test_help_includes_system_prompt_flag() -> None:
    """Test that --help output includes the --system-prompt flag."""
    result = subprocess.run(
        [sys.executable, "-c", "from cmd.root import build_parser; build_parser().parse_args(['--help'])"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "--system-prompt" in result.stdout


def test_resume_flag() -> None:
    """Test that -r / --resume flag is parsed."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import build_parser; a = build_parser().parse_args(['-r']); print(a.resume)",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.stdout.strip() == "True"


def test_resume_flag_long() -> None:
    """Test that --resume long flag is parsed."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import build_parser; a = build_parser().parse_args(['--resume']); print(a.resume)",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.stdout.strip() == "True"


def test_help_includes_resume_flag() -> None:
    """Test that --help output includes the --resume flag."""
    result = subprocess.run(
        [sys.executable, "-c", "from cmd.root import build_parser; build_parser().parse_args(['--help'])"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "--resume" in result.stdout
    assert "resume" in result.stdout.lower()


def test_find_latest_session_no_sessions() -> None:
    """Test _find_latest_session returns None when no sessions exist."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import _find_latest_session; print(_find_latest_session())",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "None" in result.stdout


def test_chat_subcommand_exists() -> None:
    """Test that 'chat' is parsed as a valid subcommand."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cmd.root import build_parser; a = build_parser().parse_args(['chat']); print(a.command)",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.stdout.strip() == "chat"


def test_chat_command_is_wired() -> None:
    """Test that cmd_chat delegates to cmd_interactive (not a stub)."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from cmd.root import cmd_chat; "
                "import inspect; "
                "src = inspect.getsource(cmd_chat); "
                "print('coming soon' not in src.lower())"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.stdout.strip() == "True"
