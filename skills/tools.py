"""Built-in tool skills for file operations, shell execution, and web fetching.

Inspired by Gemini CLI's built-in tools, these skills provide file read/write/edit,
shell command execution, grep-based search, and web content fetching.  Each tool
integrates with the existing hooks system (PreToolUse / PostToolUse) for safety.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# .ollamaignore support
# ---------------------------------------------------------------------------

_IGNORE_PATTERNS: list[str] | None = None


def _load_ignore_patterns() -> list[str]:
    """Load ignore patterns from .ollamaignore if it exists."""
    global _IGNORE_PATTERNS
    if _IGNORE_PATTERNS is not None:
        return _IGNORE_PATTERNS

    patterns: list[str] = []
    ignore_file = Path(".ollamaignore")
    if ignore_file.is_file():
        try:
            for line in ignore_file.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    patterns.append(stripped)
        except OSError as exc:
            logger.debug("Failed to read .ollamaignore: %s", exc)
    _IGNORE_PATTERNS = patterns
    return patterns


def is_path_ignored(path: str | Path) -> bool:
    """Check whether *path* matches any pattern in ``.ollamaignore``.

    Supports file glob patterns (``*.env``) and trailing-slash directory
    patterns (``secrets/``) which match any path under that directory.
    """
    patterns = _load_ignore_patterns()
    path_obj = Path(path)
    try:
        rel_path = os.path.relpath(path_obj, start=os.getcwd())
    except ValueError:
        rel_path = str(path_obj)
    rel_path = os.path.normpath(rel_path)
    basename = path_obj.name

    for pattern in patterns:
        if not pattern:
            continue
        # Directory-style pattern (e.g. "secrets/") – match any path under that directory
        if pattern.endswith("/"):
            dir_pat = os.path.normpath(pattern.rstrip("/"))
            if rel_path == dir_pat or rel_path.startswith(dir_pat + os.sep):
                return True
            continue
        # Fallback to fnmatch semantics for file/glob patterns
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(basename, pattern):
            return True
    return False


def clear_ignore_cache() -> None:
    """Reset the cached ``.ollamaignore`` patterns so they are reloaded on next access."""
    global _IGNORE_PATTERNS
    _IGNORE_PATTERNS = None


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

# File extensions searched by grep_search.  Extend this tuple to include
# additional file types in project-wide searches.
_GREP_INCLUDE_EXTENSIONS: tuple[str, ...] = (
    "*.py",
    "*.md",
    "*.txt",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.toml",
    "*.cfg",
    "*.ini",
    "*.js",
    "*.ts",
    "*.html",
    "*.css",
)


def tool_file_read(path: str, *, max_lines: int = 500) -> dict[str, Any]:
    """Read the contents of a file.

    Non-UTF-8 bytes are replaced with U+FFFD so binary files can still
    be partially inspected without raising an exception.

    Parameters
    ----------
    path:
        Path to the file to read.
    max_lines:
        Maximum number of lines to return (default 500).

    Returns
    -------
    Dict with ``content``, ``lines``, and ``path`` on success,
    or ``error`` on failure.
    """
    if is_path_ignored(path):
        return {"error": f"Path is ignored by .ollamaignore: {path}"}
    target = Path(path)
    if not target.is_file():
        return {"error": f"File not found: {path}"}
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines])
            text += f"\n... ({len(lines) - max_lines} more lines)"
        return {"content": text, "lines": len(lines), "path": str(target)}
    except OSError as exc:
        return {"error": f"Cannot read file: {exc}"}


def tool_file_write(path: str, content: str) -> dict[str, Any]:
    """Write content to a file (creates parent directories as needed).

    Parameters
    ----------
    path:
        Destination path.
    content:
        Text content to write.

    Returns
    -------
    Dict with ``path`` and ``bytes_written`` on success, or ``error``.
    """
    if is_path_ignored(path):
        return {"error": f"Path is ignored by .ollamaignore: {path}"}
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"path": str(target), "bytes_written": len(content.encode("utf-8"))}
    except OSError as exc:
        return {"error": f"Cannot write file: {exc}"}


def tool_file_edit(path: str, old_text: str, new_text: str) -> dict[str, Any]:
    """Replace the first occurrence of *old_text* with *new_text* in a file.

    Parameters
    ----------
    path:
        File to edit.
    old_text:
        Text to find and replace.
    new_text:
        Replacement text.

    Returns
    -------
    Dict with ``path`` and ``replaced`` flag, or ``error``.
    """
    if is_path_ignored(path):
        return {"error": f"Path is ignored by .ollamaignore: {path}"}
    target = Path(path)
    if not target.is_file():
        return {"error": f"File not found: {path}"}
    try:
        text = target.read_text(encoding="utf-8")
        if old_text not in text:
            return {"error": "Old text not found in file", "path": str(target)}
        new = text.replace(old_text, new_text, 1)
        target.write_text(new, encoding="utf-8")
        return {"path": str(target), "replaced": True}
    except OSError as exc:
        return {"error": f"Cannot edit file: {exc}"}


def tool_grep_search(
    pattern: str,
    path: str = ".",
    *,
    max_results: int = 50,
) -> dict[str, Any]:
    """Search for *pattern* in files under *path* using grep.

    Parameters
    ----------
    pattern:
        Text or regex pattern to search for.
    path:
        Directory or file to search in.
    max_results:
        Maximum number of matching lines to return.

    Returns
    -------
    Dict with ``matches`` list and ``count``, or ``error``.
    """
    if is_path_ignored(path):
        return {"error": f"Path is ignored by .ollamaignore: {path}"}
    try:
        include_args = [f"--include={ext}" for ext in _GREP_INCLUDE_EXTENSIONS]
        proc = subprocess.run(
            ["grep", "-rn", *include_args, pattern, path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            lines = proc.stdout.strip().splitlines()
            matches = lines[:max_results]
            return {"matches": matches, "count": len(lines), "truncated": len(lines) > max_results}
        if proc.returncode == 1:
            # grep exit code 1 means "no matches found"
            return {"matches": [], "count": 0, "truncated": False}
        stderr = proc.stderr.strip() if proc.stderr else ""
        error_msg = f"Search failed with exit code {proc.returncode}"
        if stderr:
            error_msg = f"{error_msg}: {stderr}"
        return {"error": error_msg}
    except FileNotFoundError:
        return {"error": "grep not available on this system"}
    except subprocess.TimeoutExpired:
        return {"error": "Search timed out"}
    except OSError as exc:
        return {"error": f"Search failed: {exc}"}


def tool_shell_exec(
    command: str,
    *,
    timeout: int = 30,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Execute a shell command and return the output.

    Parameters
    ----------
    command:
        Shell command to run.
    timeout:
        Maximum seconds to wait for completion.
    cwd:
        Working directory (defaults to current directory).

    Returns
    -------
    Dict with ``stdout``, ``stderr``, ``returncode``, or ``error``.
    """
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env={**os.environ},
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except OSError as exc:
        return {"error": f"Command failed: {exc}"}


def tool_web_fetch(url: str, *, max_length: int = 5000) -> dict[str, Any]:
    """Fetch content from a URL.

    Parameters
    ----------
    url:
        URL to fetch.
    max_length:
        Maximum characters to return from the response body.

    Returns
    -------
    Dict with ``content``, ``status_code``, ``url``, or ``error``.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx not installed"}

    try:
        resp = httpx.get(url, timeout=15.0, follow_redirects=True, max_redirects=5)
        body = resp.text
        if len(body) > max_length:
            body = body[:max_length] + f"\n... (truncated at {max_length} chars)"
        return {"content": body, "status_code": resp.status_code, "url": str(resp.url)}
    except httpx.HTTPError as exc:
        return {"error": f"HTTP error: {exc}"}
    except Exception as exc:
        return {"error": f"Fetch failed: {exc}"}


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOLS: dict[str, dict[str, Any]] = {
    "file_read": {
        "function": tool_file_read,
        "description": "Read file contents",
        "risk": "low",
    },
    "file_write": {
        "function": tool_file_write,
        "description": "Write content to a file",
        "risk": "medium",
    },
    "file_edit": {
        "function": tool_file_edit,
        "description": "Edit a file (find and replace)",
        "risk": "medium",
    },
    "grep_search": {
        "function": tool_grep_search,
        "description": "Search for patterns in files",
        "risk": "low",
    },
    "shell_exec": {
        "function": tool_shell_exec,
        "description": "Execute a shell command",
        "risk": "high",
    },
    "web_fetch": {
        "function": tool_web_fetch,
        "description": "Fetch content from a URL",
        "risk": "low",
    },
}


def get_tool(name: str) -> dict[str, Any] | None:
    """Look up a tool by name.

    Returns
    -------
    The tool entry dict (with ``function``, ``description``, ``risk``)
    or ``None`` if not found.
    """
    return TOOLS.get(name)


def list_tools() -> list[dict[str, str]]:
    """Return a summary of all available tools."""
    return [{"name": name, "description": info["description"], "risk": info["risk"]} for name, info in TOOLS.items()]
