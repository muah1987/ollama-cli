"""Tests for skills/tools.py -- Built-in tool skills."""

from __future__ import annotations



from skills.tools import (
    clear_ignore_cache,
    is_path_ignored,
    tool_file_edit,
    tool_file_read,
    tool_file_write,
    tool_grep_search,
    tool_shell_exec,
)


# ---------------------------------------------------------------------------
# .ollamaignore tests
# ---------------------------------------------------------------------------


class TestIgnorePatterns:
    def test_clear_and_load(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        assert is_path_ignored("anything.py") is False

    def test_ignore_file_pattern(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ollamaignore").write_text("*.env\nsecrets/\n", encoding="utf-8")
        clear_ignore_cache()
        assert is_path_ignored(".env") is True
        assert is_path_ignored("my.env") is True
        assert is_path_ignored("app.py") is False

    def test_ignore_dir_pattern(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ollamaignore").write_text("secrets/\n", encoding="utf-8")
        (tmp_path / "secrets").mkdir()
        clear_ignore_cache()
        assert is_path_ignored("secrets/key.txt") is True

    def test_ignore_comment_lines(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ollamaignore").write_text("# comment\n*.log\n", encoding="utf-8")
        clear_ignore_cache()
        assert is_path_ignored("debug.log") is True
        assert is_path_ignored("# comment") is False


# ---------------------------------------------------------------------------
# tool_file_read
# ---------------------------------------------------------------------------


class TestToolFileRead:
    def test_read_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        (tmp_path / "hello.txt").write_text("Hello, world!", encoding="utf-8")
        result = tool_file_read("hello.txt")
        assert "content" in result
        assert result["content"] == "Hello, world!"
        assert result["lines"] == 1

    def test_read_nonexistent_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        result = tool_file_read("nonexistent.txt")
        assert "error" in result

    def test_read_max_lines(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        content = "\n".join(f"line {i}" for i in range(600))
        (tmp_path / "big.txt").write_text(content, encoding="utf-8")
        result = tool_file_read("big.txt", max_lines=10)
        assert "content" in result
        assert "more lines" in result["content"]

    def test_read_ignored_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ollamaignore").write_text("*.secret\n", encoding="utf-8")
        (tmp_path / "key.secret").write_text("s3cr3t", encoding="utf-8")
        clear_ignore_cache()
        result = tool_file_read("key.secret")
        assert "error" in result
        assert "ignored" in result["error"].lower()


# ---------------------------------------------------------------------------
# tool_file_write
# ---------------------------------------------------------------------------


class TestToolFileWrite:
    def test_write_new_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        result = tool_file_write("output.txt", "hello world")
        assert "path" in result
        assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "hello world"

    def test_write_creates_dirs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        result = tool_file_write("sub/dir/file.txt", "content")
        assert "path" in result
        assert (tmp_path / "sub" / "dir" / "file.txt").exists()

    def test_write_ignored_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ollamaignore").write_text("*.secret\n", encoding="utf-8")
        clear_ignore_cache()
        result = tool_file_write("data.secret", "content")
        assert "error" in result


# ---------------------------------------------------------------------------
# tool_file_edit
# ---------------------------------------------------------------------------


class TestToolFileEdit:
    def test_edit_replace(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        (tmp_path / "app.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
        result = tool_file_edit("app.py", "return 'hi'", "return 'hello'")
        assert result.get("replaced") is True
        content = (tmp_path / "app.py").read_text(encoding="utf-8")
        assert "return 'hello'" in content

    def test_edit_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        (tmp_path / "app.py").write_text("existing content", encoding="utf-8")
        result = tool_file_edit("app.py", "nonexistent text", "new text")
        assert "error" in result

    def test_edit_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        result = tool_file_edit("nope.py", "old", "new")
        assert "error" in result


# ---------------------------------------------------------------------------
# tool_grep_search
# ---------------------------------------------------------------------------


class TestToolGrepSearch:
    def test_grep_finds_match(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        (tmp_path / "test.py").write_text("def hello():\n    pass\n", encoding="utf-8")
        result = tool_grep_search("hello", str(tmp_path))
        assert "matches" in result
        assert len(result["matches"]) > 0

    def test_grep_no_match(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        (tmp_path / "test.py").write_text("nothing here\n", encoding="utf-8")
        result = tool_grep_search("xyzneverexists", str(tmp_path))
        matches = result.get("matches", [])
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# tool_shell_exec
# ---------------------------------------------------------------------------


class TestToolShellExec:
    def test_shell_echo(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        result = tool_shell_exec("echo hello")
        assert "stdout" in result
        assert "hello" in result["stdout"]

    def test_shell_failing_command(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        clear_ignore_cache()
        result = tool_shell_exec("false")
        assert result.get("returncode", 0) != 0
