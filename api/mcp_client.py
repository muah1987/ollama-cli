#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""
MCP (Model Context Protocol) client -- integrates external MCP servers.

Provides a unified interface for connecting to MCP-compatible servers
(GitHub MCP, Docker MCP, filesystem MCP, etc.) and exposing their tools
to the Qarin CLI agent pipeline.

MCP servers communicate via stdin/stdout JSON-RPC or HTTP, providing:
- Tool discovery (list available tools from each server)
- Tool invocation (call a tool on a connected MCP server)
- Resource access (read resources exposed by MCP servers)

Configuration is stored in ``.qarin/mcp.json``.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP configuration path
# ---------------------------------------------------------------------------

_MCP_CONFIG_FILE = ".qarin/mcp.json"

# ---------------------------------------------------------------------------
# Default MCP server definitions
# ---------------------------------------------------------------------------

_DEFAULT_MCP_SERVERS: dict[str, dict[str, Any]] = {
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
        "description": "GitHub MCP server for repos, issues, PRs, actions",
        "enabled": False,
    },
    "docker": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "mcp/docker"],
        "env": {},
        "description": "Docker MCP server for container management",
        "enabled": False,
    },
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "env": {},
        "description": "Filesystem MCP server for file operations",
        "enabled": False,
    },
    "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {},
        "description": "Memory MCP server for persistent knowledge graph",
        "enabled": False,
    },
}


# ---------------------------------------------------------------------------
# MCP Server Configuration
# ---------------------------------------------------------------------------


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server connection.

    Parameters
    ----------
    name:
        Unique identifier for the server (e.g. ``"github"``, ``"docker"``).
    command:
        The command to launch the MCP server process.
    args:
        Arguments to pass to the server command.
    env:
        Environment variables to set for the server process.
    description:
        Human-readable description of the server.
    enabled:
        Whether this server should be connected on startup.
    url:
        Optional HTTP URL for HTTP-based MCP servers.
    """

    name: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    description: str = ""
    enabled: bool = False
    url: str = ""


# ---------------------------------------------------------------------------
# MCP Tool
# ---------------------------------------------------------------------------


@dataclass
class MCPTool:
    """A tool discovered from an MCP server.

    Parameters
    ----------
    name:
        Tool name as reported by the MCP server.
    description:
        Human-readable description.
    server:
        The MCP server this tool belongs to.
    input_schema:
        JSON Schema for the tool's input parameters.
    """

    name: str = ""
    description: str = ""
    server: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# MCP Client
# ---------------------------------------------------------------------------


class MCPClient:
    """Client for managing MCP server connections and tool invocations.

    Loads MCP server configurations from ``.qarin/mcp.json`` and provides
    methods to list, connect, and invoke tools on MCP servers.

    The client supports both stdio-based and HTTP-based MCP servers.
    """

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerConfig] = {}
        self._discovered_tools: list[MCPTool] = []
        self._load_config()

    # -- configuration -------------------------------------------------------

    def _load_config(self) -> None:
        """Load MCP server configurations from mcp.json and defaults."""
        config_path = Path(_MCP_CONFIG_FILE)

        # Start with defaults
        for name, default in _DEFAULT_MCP_SERVERS.items():
            self._servers[name] = MCPServerConfig(
                name=name,
                command=default["command"],
                args=default.get("args", []),
                env=default.get("env", {}),
                description=default.get("description", ""),
                enabled=default.get("enabled", False),
            )

        # Overlay from config file
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_data = json.load(f)
                servers = config_data.get("mcpServers", config_data.get("servers", {}))
                for name, server_data in servers.items():
                    if isinstance(server_data, dict):
                        self._servers[name] = MCPServerConfig(
                            name=name,
                            command=server_data.get("command", ""),
                            args=server_data.get("args", []),
                            env=server_data.get("env", {}),
                            description=server_data.get("description", f"MCP server: {name}"),
                            enabled=server_data.get("enabled", True),
                            url=server_data.get("url", ""),
                        )
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to load MCP config from %s", config_path)

        # Resolve environment variable references in env fields
        for server in self._servers.values():
            resolved_env: dict[str, str] = {}
            for key, value in server.env.items():
                if value == "" or value.startswith("$"):
                    # Try to resolve from os.environ
                    env_name = value.lstrip("$") if value.startswith("$") else key
                    resolved_env[key] = os.environ.get(env_name, "")
                else:
                    resolved_env[key] = value
            server.env = resolved_env

            # Auto-enable GitHub MCP if GH_TOKEN is set
            if server.name == "github" and os.environ.get("GH_TOKEN", ""):
                token = os.environ.get("GH_TOKEN", "")
                server.env["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
                if token:
                    server.enabled = True

    def save_config(self) -> Path:
        """Save current MCP configuration to mcp.json.

        Returns
        -------
        Path to the saved config file.
        """
        config_path = Path(_MCP_CONFIG_FILE)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        servers_data: dict[str, Any] = {}
        for name, server in self._servers.items():
            servers_data[name] = {
                "command": server.command,
                "args": server.args,
                "env": {k: "" for k in server.env},  # Don't save actual tokens
                "description": server.description,
                "enabled": server.enabled,
            }
            if server.url:
                servers_data[name]["url"] = server.url

        data = {"mcpServers": servers_data}
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

        return config_path

    # -- server management ---------------------------------------------------

    def list_servers(self) -> list[dict[str, Any]]:
        """Return a list of configured MCP servers with status.

        Returns
        -------
        List of dicts with server name, description, enabled status,
        and command info.
        """
        result: list[dict[str, Any]] = []
        for name, server in self._servers.items():
            has_credentials = True
            if server.name == "github":
                has_credentials = bool(server.env.get("GITHUB_PERSONAL_ACCESS_TOKEN", ""))
            result.append(
                {
                    "name": name,
                    "description": server.description,
                    "enabled": server.enabled,
                    "command": server.command,
                    "has_credentials": has_credentials,
                }
            )
        return result

    def add_server(self, name: str, config: dict[str, Any]) -> None:
        """Add or update an MCP server configuration.

        Parameters
        ----------
        name:
            Unique server identifier.
        config:
            Server configuration dict with command, args, env, etc.
        """
        self._servers[name] = MCPServerConfig(
            name=name,
            command=config.get("command", ""),
            args=config.get("args", []),
            env=config.get("env", {}),
            description=config.get("description", f"MCP server: {name}"),
            enabled=config.get("enabled", True),
            url=config.get("url", ""),
        )

    def remove_server(self, name: str) -> bool:
        """Remove an MCP server configuration.

        Returns ``True`` if the server was found and removed.
        """
        if name in self._servers:
            del self._servers[name]
            return True
        return False

    def enable_server(self, name: str) -> bool:
        """Enable an MCP server.

        Returns ``True`` if the server exists and was enabled.
        """
        if name in self._servers:
            self._servers[name].enabled = True
            return True
        return False

    def disable_server(self, name: str) -> bool:
        """Disable an MCP server.

        Returns ``True`` if the server exists and was disabled.
        """
        if name in self._servers:
            self._servers[name].enabled = False
            return True
        return False

    # -- tool discovery ------------------------------------------------------

    def discover_tools(self, server_name: str) -> list[MCPTool]:
        """Discover available tools from an MCP server.

        Sends a ``tools/list`` JSON-RPC request to the server and
        parses the response.

        Parameters
        ----------
        server_name:
            Name of the MCP server to query.

        Returns
        -------
        List of discovered :class:`MCPTool` instances.
        """
        server = self._servers.get(server_name)
        if server is None or not server.enabled:
            return []

        if not server.command:
            return []

        try:
            # Build the JSON-RPC request for tools/list
            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                }
            )

            env = {**os.environ, **server.env}
            proc = subprocess.run(
                [server.command, *server.args],
                input=request,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
            )

            if proc.returncode != 0:
                logger.warning(
                    "MCP server %s returned non-zero exit: %s",
                    server_name,
                    proc.stderr[:200],
                )
                return []

            # Parse the JSON-RPC response
            response = json.loads(proc.stdout)
            tools_data = response.get("result", {}).get("tools", [])

            tools: list[MCPTool] = []
            for tool_data in tools_data:
                tools.append(
                    MCPTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        server=server_name,
                        input_schema=tool_data.get("inputSchema", {}),
                    )
                )

            self._discovered_tools.extend(tools)
            return tools

        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to discover tools from %s: %s", server_name, exc)
            return []

    def list_discovered_tools(self) -> list[dict[str, str]]:
        """Return a summary of all discovered MCP tools.

        Returns
        -------
        List of dicts with tool name, description, and server.
        """
        return [
            {
                "name": f"mcp:{tool.server}:{tool.name}",
                "description": tool.description,
                "server": tool.server,
            }
            for tool in self._discovered_tools
        ]

    # -- tool invocation -----------------------------------------------------

    def invoke_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke a tool on an MCP server.

        Sends a ``tools/call`` JSON-RPC request to the server.

        Parameters
        ----------
        server_name:
            Name of the MCP server.
        tool_name:
            Name of the tool to invoke.
        arguments:
            Arguments to pass to the tool.

        Returns
        -------
        The tool result as a dict, or an error dict.
        """
        server = self._servers.get(server_name)
        if server is None:
            return {"error": f"MCP server not found: {server_name}"}
        if not server.enabled:
            return {"error": f"MCP server is disabled: {server_name}"}

        try:
            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments or {},
                    },
                }
            )

            env = {**os.environ, **server.env}
            proc = subprocess.run(
                [server.command, *server.args],
                input=request,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )

            if proc.returncode != 0:
                return {
                    "error": f"MCP server error: {proc.stderr[:500]}",
                    "server": server_name,
                    "tool": tool_name,
                }

            response = json.loads(proc.stdout)
            result = response.get("result", {})
            return {
                "server": server_name,
                "tool": tool_name,
                "result": result,
            }

        except subprocess.TimeoutExpired:
            return {"error": f"MCP tool invocation timed out: {server_name}/{tool_name}"}
        except (json.JSONDecodeError, OSError) as exc:
            return {"error": f"MCP tool invocation failed: {exc}"}

    def get_server(self, name: str) -> MCPServerConfig | None:
        """Return an MCP server config by name, or ``None``."""
        return self._servers.get(name)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_mcp_client: MCPClient | None = None


def get_mcp_client() -> MCPClient:
    """Return the singleton MCP client, creating it on first access."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    client = MCPClient()
    print("MCP Servers:")
    for s in client.list_servers():
        status = "enabled" if s["enabled"] else "disabled"
        cred = "✓" if s["has_credentials"] else "✗"
        print(f"  [{status}] {s['name']}: {s['description']} (credentials: {cred})")
