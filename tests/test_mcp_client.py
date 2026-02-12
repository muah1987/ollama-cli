"""
Tests for the MCP (Model Context Protocol) client module.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = str(Path(__file__).parent.parent)


# ---------------------------------------------------------------------------
# MCP Client tests
# ---------------------------------------------------------------------------


class TestMCPClient:
    """Tests for MCPClient initialization, server management, and singleton."""

    def test_mcp_client_module_exists(self) -> None:
        """api/mcp_client.py should exist on disk."""
        module_path = Path(__file__).parent.parent / "api" / "mcp_client.py"
        assert module_path.is_file()

    def test_mcp_client_default_servers(self) -> None:
        """MCPClient() should have at least 4 default servers."""
        from api.mcp_client import MCPClient

        client = MCPClient()
        servers = client.list_servers()
        assert len(servers) >= 4
        names = {s["name"] for s in servers}
        assert "github" in names
        assert "docker" in names
        assert "filesystem" in names
        assert "memory" in names

    def test_list_servers(self) -> None:
        """list_servers() should return dicts with expected keys."""
        from api.mcp_client import MCPClient

        client = MCPClient()
        servers = client.list_servers()
        assert isinstance(servers, list)
        for server in servers:
            assert "name" in server
            assert "description" in server
            assert "enabled" in server
            assert "command" in server

    def test_add_server(self) -> None:
        """add_server() should register a custom MCP server."""
        from api.mcp_client import MCPClient

        client = MCPClient()
        client.add_server("custom", {
            "command": "node",
            "args": ["server.js"],
            "description": "Custom MCP test server",
            "enabled": True,
        })
        names = {s["name"] for s in client.list_servers()}
        assert "custom" in names

        cfg = client.get_server("custom")
        assert cfg is not None
        assert cfg.command == "node"
        assert cfg.enabled is True

    def test_remove_server(self) -> None:
        """remove_server() should remove a registered MCP server."""
        from api.mcp_client import MCPClient

        client = MCPClient()
        client.add_server("temp", {"command": "echo", "description": "temporary"})
        assert client.remove_server("temp") is True
        assert client.get_server("temp") is None
        assert client.remove_server("nonexistent") is False

    def test_enable_disable_server(self) -> None:
        """enable_server() and disable_server() should toggle enabled flag."""
        from api.mcp_client import MCPClient

        client = MCPClient()
        # Default servers start disabled
        server = client.get_server("docker")
        assert server is not None
        assert server.enabled is False

        assert client.enable_server("docker") is True
        assert client.get_server("docker").enabled is True

        assert client.disable_server("docker") is True
        assert client.get_server("docker").enabled is False

        # Non-existent server returns False
        assert client.enable_server("nonexistent") is False
        assert client.disable_server("nonexistent") is False

    def test_github_auto_enable_with_gh_token(self) -> None:
        """When GH_TOKEN env is set, github server should be auto-enabled."""
        from api.mcp_client import MCPClient

        with patch.dict(os.environ, {"GH_TOKEN": "test-token-value"}, clear=False):
            client = MCPClient()
            server = client.get_server("github")
            assert server is not None
            assert server.enabled is True
            assert server.env.get("GITHUB_PERSONAL_ACCESS_TOKEN") == "test-token-value"

    def test_get_mcp_client_singleton(self) -> None:
        """get_mcp_client() should return the same instance on repeated calls."""
        import api.mcp_client as mcp_mod
        from api.mcp_client import get_mcp_client

        # Reset singleton so the test is deterministic
        mcp_mod._mcp_client = None
        try:
            a = get_mcp_client()
            b = get_mcp_client()
            assert a is b
        finally:
            mcp_mod._mcp_client = None


# ---------------------------------------------------------------------------
# MCP Config file tests
# ---------------------------------------------------------------------------


class TestMCPConfig:
    """Tests for the .ollama/mcp.json configuration file."""

    def test_mcp_config_file_exists(self) -> None:
        """.ollama/mcp.json should exist on disk."""
        config_path = Path(__file__).parent.parent / ".ollama" / "mcp.json"
        assert config_path.is_file()

    def test_mcp_config_has_servers(self) -> None:
        """mcp.json should have mcpServers key with expected entries."""
        config_path = Path(__file__).parent.parent / ".ollama" / "mcp.json"
        with open(config_path) as f:
            data = json.load(f)

        servers = data.get("mcpServers", {})
        assert "github" in servers
        assert "docker" in servers
        assert "filesystem" in servers
        assert "memory" in servers


# ---------------------------------------------------------------------------
# MCP command registration tests (subprocess to avoid cmd module collision)
# ---------------------------------------------------------------------------


class TestMCPCommandRegistered:
    """Tests for /mcp command registration in InteractiveMode."""

    def test_mcp_command_in_command_table(self) -> None:
        """/mcp should be registered in InteractiveMode._COMMAND_TABLE."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from cmd.interactive import InteractiveMode; "
                    "print('/mcp' in InteractiveMode._COMMAND_TABLE)"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "True"
