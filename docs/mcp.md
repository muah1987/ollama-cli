# MCP Integration

Connect Ollama CLI to MCP (Model Context Protocol) servers for extended capabilities.

---

## Overview

MCP servers provide additional tools and resources to the CLI via the
[Model Context Protocol](https://modelcontextprotocol.io/). Each server
exposes tools that can be discovered and invoked from the interactive REPL.

Ollama CLI ships with four built-in MCP server definitions:

| Server | Description | Auto-enable |
|--------|-------------|-------------|
| `github` | GitHub repos, issues, PRs, actions | Yes (when `GH_TOKEN` is set) |
| `docker` | Container management | No |
| `filesystem` | File operations | No |
| `memory` | Persistent knowledge graph | No |

---

## Configuration

MCP servers are configured in `.ollama/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": ""
      },
      "description": "GitHub MCP server",
      "enabled": false
    },
    "docker": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/docker"],
      "description": "Docker MCP server",
      "enabled": false
    }
  }
}
```

### GitHub MCP (Auto-enable)

When `GH_TOKEN` is set in your environment or `.env` file, the GitHub MCP
server is automatically enabled and the token is passed as
`GITHUB_PERSONAL_ACCESS_TOKEN`.

```bash
# In your .env file
GH_TOKEN=ghp_your_github_token
```

### Docker MCP

Requires Docker to be installed. The MCP server runs as a container:

```bash
# Enable Docker MCP
>>> /mcp enable docker
```

### Custom MCP Servers

Add any MCP-compatible server to `.ollama/mcp.json`:

```json
{
  "mcpServers": {
    "my_server": {
      "command": "path/to/my-mcp-server",
      "args": ["--some-flag"],
      "env": {"MY_API_KEY": ""},
      "description": "My custom MCP server",
      "enabled": true
    }
  }
}
```

---

## REPL Commands

| Command | Description |
|---------|-------------|
| `/mcp` | List all configured MCP servers with status |
| `/mcp enable <name>` | Enable an MCP server |
| `/mcp disable <name>` | Disable an MCP server |
| `/mcp tools [name]` | Discover tools from an MCP server |
| `/mcp invoke <server> <tool> [json]` | Invoke an MCP tool |

### Examples

```bash
# List servers
>>> /mcp
  ● enabled  github   GitHub MCP server  [cred: ✓]
  ○ disabled docker   Docker MCP server  [cred: ✗]

# Discover tools
>>> /mcp tools github
  list_repos              List repositories
  get_issue               Get issue details
  create_pull_request     Create a pull request
  ...

# Invoke a tool
>>> /mcp invoke github get_issue '{"owner": "myorg", "repo": "myrepo", "issue_number": 42}'
```

---

## Architecture

MCP servers communicate via JSON-RPC over stdin/stdout:

```
┌──────────────┐   JSON-RPC    ┌──────────────┐
│  Ollama CLI  │ ───stdin───▶  │  MCP Server  │
│  /mcp cmd    │ ◀──stdout──── │  (npx/docker) │
└──────────────┘               └──────────────┘
```

The `MCPClient` class (`api/mcp_client.py`) manages:
- Server configuration loading/saving
- Tool discovery (`tools/list`)
- Tool invocation (`tools/call`)
- Credential resolution from environment variables

---

## Security

- API tokens are never persisted to `mcp.json` — only empty placeholder keys
- Tokens are resolved from environment variables at runtime
- MCP servers run as subprocesses with timeouts (15s for discovery, 30s for invocation)
- The `PermissionRequest` hook can audit MCP tool invocations
