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


def _resolve_search_provider_and_key(provider: str | None) -> tuple[str, str]:
    """Resolve search provider/key from explicit provider and environment variables."""
    resolved_provider = (provider or os.environ.get("SEARCH_API_PROVIDER", "tavily")).strip().lower()
    resolved_key = os.environ.get("SEARCH_API_KEY", "").strip()
    return resolved_provider, resolved_key


def tool_web_search(
    query: str,
    *,
    provider: str = "",
    api_key: str = "",
    max_results: int = 5,
) -> dict[str, Any]:
    """Search the web using a provider API key (Tavily or Serper)."""
    if (api_key or "").strip():
        return {"error": "api_key argument is not supported; use SEARCH_API_KEY environment variable"}
    if not query.strip():
        return {"error": "No search query provided"}
    resolved_provider, resolved_key = _resolve_search_provider_and_key(provider)
    if not resolved_key:
        return {"error": "SEARCH_API_KEY is not set"}

    try:
        import httpx
    except ImportError:
        return {"error": "httpx not installed"}

    try:
        if resolved_provider == "tavily":
            resp = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": resolved_key,
                    "query": query,
                    "max_results": max(1, min(max_results, 20)),
                },
                timeout=20.0,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            normalized = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in results
            ]
            return {"provider": resolved_provider, "query": query, "results": normalized}

        if resolved_provider in {"serper", "google-serper"}:
            resp = httpx.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": resolved_key},
                json={"q": query, "num": max(1, min(max_results, 10))},
                timeout=20.0,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("organic", [])
            normalized = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("link", ""),
                    "content": r.get("snippet", ""),
                }
                for r in results
            ]
            return {"provider": resolved_provider, "query": query, "results": normalized}

        return {"error": f"Unsupported search provider: {resolved_provider}"}
    except Exception as exc:
        return {"error": f"Search failed: {exc}"}


def tool_web_crawler(
    url: str,
    *,
    provider: str = "",
    api_key: str = "",
    max_length: int = 5000,
) -> dict[str, Any]:
    """Crawl a URL using provider API (currently Tavily extract API)."""
    if (api_key or "").strip():
        return {"error": "api_key argument is not supported; use SEARCH_API_KEY environment variable"}
    if not url.strip():
        return {"error": "No URL provided"}
    resolved_provider, resolved_key = _resolve_search_provider_and_key(provider)
    if not resolved_key:
        return {"error": "SEARCH_API_KEY is not set"}
    if resolved_provider != "tavily":
        return {"error": f"Unsupported crawler provider: {resolved_provider}"}

    try:
        import httpx
    except ImportError:
        return {"error": "httpx not installed"}

    try:
        resp = httpx.post(
            "https://api.tavily.com/extract",
            json={"api_key": resolved_key, "urls": [url]},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        first = results[0] if results else {}
        content = str(first.get("raw_content", "") or first.get("content", ""))
        if len(content) > max_length:
            content = content[:max_length] + f"\n... (truncated at {max_length} chars)"
        return {"provider": resolved_provider, "url": url, "content": content}
    except Exception as exc:
        return {"error": f"Crawl failed: {exc}"}


def tool_meta_crawler(
    query: str,
    *,
    provider: str = "",
    api_key: str = "",
    max_results: int = 3,
    max_length: int = 2000,
) -> dict[str, Any]:
    """Run search then crawl top results with the same provider API."""
    if (api_key or "").strip():
        return {"error": "api_key argument is not supported; use SEARCH_API_KEY environment variable"}
    search_result = tool_web_search(query, provider=provider, api_key="", max_results=max_results)
    if "error" in search_result:
        return search_result
    resolved_provider = str(search_result.get("provider", provider)).strip().lower()
    if resolved_provider != "tavily":
        return {"error": f"Unsupported meta crawler provider: {resolved_provider}"}
    crawled: list[dict[str, Any]] = []
    for item in search_result.get("results", []):
        target_url = str(item.get("url", "")).strip()
        if not target_url:
            continue
        crawl_result = tool_web_crawler(target_url, provider=resolved_provider, max_length=max_length)
        crawled.append(
            {
                "title": item.get("title", ""),
                "url": target_url,
                "content": crawl_result.get("content", ""),
                "error": crawl_result.get("error"),
            }
        )
    return {"provider": resolved_provider, "query": query, "results": crawled}


def tool_model_pull(model_name: str, *, force: bool = False) -> dict[str, Any]:
    """Pull (download) a model from the Ollama registry.

    When *force* is ``True``, the model is deleted first and then re-pulled
    so that a fresh copy is downloaded even if it already exists locally.

    Parameters
    ----------
    model_name:
        Name of the model to pull (e.g. ``llama3.2``, ``codestral:latest``).
    force:
        If ``True``, delete the existing local copy before pulling.

    Returns
    -------
    Dict with ``model``, ``status``, and ``messages`` on success, or ``error``.
    """
    if not model_name or not model_name.strip():
        return {"error": "No model name provided"}

    model_name = model_name.strip()

    try:
        import httpx
    except ImportError:
        return {"error": "httpx not installed"}

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    # Force mode: delete existing model first
    if force:
        try:
            resp = httpx.request("DELETE", f"{host}/api/delete", json={"name": model_name}, timeout=30.0)
            if resp.status_code == 200:
                logger.info("Deleted existing model %s for force-pull", model_name)
            elif resp.status_code == 404:
                pass  # Model didn't exist locally, that's fine
            else:
                logger.debug("Delete returned status %d for %s", resp.status_code, model_name)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            return {"error": f"Cannot connect to Ollama at {host}: {exc}"}

    # Pull the model (non-streaming to collect final status)
    try:
        resp = httpx.post(
            f"{host}/api/pull",
            json={"name": model_name, "stream": True},
            timeout=None,
        )
        resp.raise_for_status()
    except httpx.ConnectError:
        return {"error": f"Cannot connect to Ollama at {host}. Is Ollama running?"}
    except httpx.HTTPStatusError as exc:
        return {"error": f"Pull failed with HTTP {exc.response.status_code}"}

    # Parse streamed NDJSON lines for status messages
    import json as _json

    messages: list[str] = []
    final_status = "unknown"
    for line in resp.text.strip().splitlines():
        if not line:
            continue
        try:
            data = _json.loads(line)
        except _json.JSONDecodeError:
            continue
        status = data.get("status", "")
        if status and status not in messages:
            messages.append(status)
        if status == "success":
            final_status = "success"

    return {
        "model": model_name,
        "status": final_status,
        "force": force,
        "messages": messages,
    }


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOLS: dict[str, dict[str, Any]] = {
    "file_read": {
        "function": tool_file_read,
        "description": "Read file contents",
        "risk": "low",
        "arg_map": lambda a: (a.get("path", ""),),
        "kwarg_map": lambda a: {},
    },
    "file_write": {
        "function": tool_file_write,
        "description": "Write content to a file",
        "risk": "medium",
        "arg_map": lambda a: (a.get("path", ""), a.get("content", "")),
        "kwarg_map": lambda a: {},
    },
    "file_edit": {
        "function": tool_file_edit,
        "description": "Edit a file (find and replace)",
        "risk": "medium",
        "arg_map": lambda a: (a.get("path", ""), a.get("old_text", ""), a.get("new_text", "")),
        "kwarg_map": lambda a: {},
    },
    "grep_search": {
        "function": tool_grep_search,
        "description": "Search for patterns in files",
        "risk": "low",
        "arg_map": lambda a: (a.get("pattern", ""), a.get("path", ".")),
        "kwarg_map": lambda a: {},
    },
    "shell_exec": {
        "function": tool_shell_exec,
        "description": "Execute a shell command",
        "risk": "high",
        "arg_map": lambda a: (a.get("command", ""),),
        "kwarg_map": lambda a: {},
    },
    "web_fetch": {
        "function": tool_web_fetch,
        "description": "Fetch content from a URL",
        "risk": "low",
        "arg_map": lambda a: (a.get("url", ""),),
        "kwarg_map": lambda a: {},
    },
    "web_search": {
        "function": tool_web_search,
        "description": "Search the web using SEARCH_API_KEY-backed providers",
        "risk": "low",
        "arg_map": lambda a: (a.get("query", ""),),
        "kwarg_map": lambda a: {
            "provider": a.get("provider", ""),
            "max_results": a.get("max_results", 5),
        },
    },
    "web_crawler": {
        "function": tool_web_crawler,
        "description": "Crawl a URL using a search API provider",
        "risk": "low",
        "arg_map": lambda a: (a.get("url", ""),),
        "kwarg_map": lambda a: {
            "provider": a.get("provider", ""),
            "max_length": a.get("max_length", 5000),
        },
    },
    "meta_crawler": {
        "function": tool_meta_crawler,
        "description": "Search then crawl top results using the provider API",
        "risk": "low",
        "arg_map": lambda a: (a.get("query", ""),),
        "kwarg_map": lambda a: {
            "provider": a.get("provider", ""),
            "max_results": a.get("max_results", 3),
            "max_length": a.get("max_length", 2000),
        },
    },
    "model_pull": {
        "function": tool_model_pull,
        "description": "Pull (download) a model from the Ollama registry",
        "risk": "medium",
        "arg_map": lambda a: (a.get("model_name", ""),),
        "kwarg_map": lambda a: {"force": a.get("force", False)},
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


def get_tools_schema() -> list[dict[str, Any]]:
    """Return Ollama-native tool definitions for all built-in tools.

    The returned list can be passed directly as the ``tools`` parameter
    in an Ollama ``/api/chat`` request so that the model can invoke tools
    natively instead of relying on text-based suggestions.

    Returns
    -------
    List of tool definition dicts in Ollama function-calling format.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "file_read",
                "description": "Read the contents of a file",
                "parameters": {
                    "type": "object",
                    "required": ["path"],
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file to read"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "file_write",
                "description": "Write content to a file (creates parent directories as needed)",
                "parameters": {
                    "type": "object",
                    "required": ["path", "content"],
                    "properties": {
                        "path": {"type": "string", "description": "Destination file path"},
                        "content": {"type": "string", "description": "Text content to write"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "file_edit",
                "description": "Replace the first occurrence of old_text with new_text in a file",
                "parameters": {
                    "type": "object",
                    "required": ["path", "old_text", "new_text"],
                    "properties": {
                        "path": {"type": "string", "description": "File to edit"},
                        "old_text": {"type": "string", "description": "Text to find and replace"},
                        "new_text": {"type": "string", "description": "Replacement text"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "grep_search",
                "description": "Search for a pattern in files under a directory using grep",
                "parameters": {
                    "type": "object",
                    "required": ["pattern"],
                    "properties": {
                        "pattern": {"type": "string", "description": "Text or regex pattern to search for"},
                        "path": {"type": "string", "description": "Directory or file to search in (default: current dir)"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "shell_exec",
                "description": "Execute a shell command and return its output",
                "parameters": {
                    "type": "object",
                    "required": ["command"],
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to run"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "Fetch content from a URL",
                "parameters": {
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web using SEARCH_API_KEY-backed providers (tavily, serper)",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "provider": {"type": "string", "description": "Search provider (default: tavily)"},
                        "max_results": {"type": "integer", "description": "Maximum search results to return"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_crawler",
                "description": "Crawl a URL using the provider API (tavily extract)",
                "parameters": {
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {"type": "string", "description": "URL to crawl"},
                        "provider": {"type": "string", "description": "Crawler provider (default: tavily)"},
                        "max_length": {"type": "integer", "description": "Maximum content length to return"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "meta_crawler",
                "description": "Search then crawl top results with the same provider API",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "provider": {"type": "string", "description": "Provider used for search/crawl"},
                        "max_results": {"type": "integer", "description": "Maximum results to crawl"},
                        "max_length": {"type": "integer", "description": "Maximum content length per crawled result"},
                    },
                },
            },
        },
    ]


def execute_tool_call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name with the given arguments.

    This is used by the session to auto-execute tool calls returned by
    the model via native function calling.  Each tool entry in ``TOOLS``
    includes ``arg_map`` and ``kwarg_map`` callables that translate the
    argument dict into positional and keyword arguments for the tool
    function, keeping dispatch generic.

    Parameters
    ----------
    tool_name:
        Name of the tool to execute (e.g. ``file_read``).
    arguments:
        Dict of keyword arguments for the tool function.

    Returns
    -------
    Tool result dict with output or ``error`` key.
    """
    entry = TOOLS.get(tool_name)
    if entry is None:
        return {"error": f"Unknown tool: {tool_name}"}

    func = entry["function"]
    arg_map = entry.get("arg_map")
    kwarg_map = entry.get("kwarg_map")

    try:
        args = arg_map(arguments) if arg_map else ()
        kwargs = kwarg_map(arguments) if kwarg_map else {}
        return func(*args, **kwargs)
    except Exception as exc:
        return {"error": str(exc)}


def fire_skill_trigger(skill_name: str, skill_params: dict[str, Any] | None = None) -> bool:
    """Fire the SkillTrigger hook for the skill→hook→.py pipeline.

    Parameters
    ----------
    skill_name:
        Name of the skill being triggered.
    skill_params:
        Parameters passed to the skill.

    Returns
    -------
    ``True`` if the skill is allowed to proceed, ``False`` if denied.
    """
    try:
        from server.hook_runner import HookRunner

        runner = HookRunner()
        if not runner.is_enabled():
            return True

        payload = {
            "skill_name": skill_name,
            "skill_params": skill_params or {},
            "trigger_source": "skill",
        }
        results = runner.run_hook("SkillTrigger", payload, timeout=10)
        for r in results:
            decision = r.permission_decision
            if decision == "deny":
                logger.info("Skill '%s' blocked by SkillTrigger hook", skill_name)
                return False
    except Exception:  # noqa: BLE001
        logger.debug("SkillTrigger hook failed, allowing skill", exc_info=True)
    return True
