[![Auto Release](https://github.com/muah1987/ollama-cli/actions/workflows/autorelease.yml/badge.svg?branch=main)](https://github.com/muah1987/ollama-cli/actions/workflows/autorelease.yml) [![Release](https://github.com/muah1987/ollama-cli/actions/workflows/release.yml/badge.svg)](https://github.com/muah1987/ollama-cli/actions/workflows/release.yml) [![Deploy to PyPI](https://github.com/muah1987/ollama-cli/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/muah1987/ollama-cli/actions/workflows/pypi-publish.yml) [![Dependabot Updates](https://github.com/muah1987/ollama-cli/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/muah1987/ollama-cli/actions/workflows/dependabot/dependabot-updates) [![Build and Test](https://github.com/muah1987/ollama-cli/actions/workflows/build-test.yml/badge.svg)](https://github.com/muah1987/ollama-cli/actions/workflows/build-test.yml)

# Ollama CLI Documentation

Comprehensive documentation for Ollama CLI - a full-featured AI coding assistant powered by Ollama with multi-provider support.

---

## Getting Started

### Quick Start Guide

1. **Install Ollama CLI** (with automatic Ollama installation):
   ```bash
   curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash
   ```

2. **Start Ollama server**:
   ```bash
   ollama serve
   ```

3. **Start chatting**:
   ```bash
   ollama-cli interactive
   ```

---

## Documentation Structure

| Documentation | Description | Link |
|-------------|-------------|------|
| **Getting Started** | Installation and first steps | [`docs/getting_started.md`](getting_started.md) |
| **Project Overview** | Features, architecture, hooks, status lines, and contributing | [`docs/project_overview.md`](project_overview.md) |
| **CLI Reference** | All available commands | [`docs/cli_reference.md`](cli_reference.md) |
| **API Reference** | Ollama and provider APIs | [`docs/api_reference.md`](api_reference.md) |
| **Configuration** | Environment variables and settings | [`docs/configuration.md`](configuration.md) |
| **Multi-Provider** | Using Claude, Gemini, Codex, HF | [`docs/multi_provider.md`](multi_provider.md) |
| **Agent Models** | Agent-specific model assignments | [`docs/agent_model_assignment.md`](agent_model_assignment.md) |
| **RDMA Support** | High-performance networking | [`docs/rdma.md`](rdma.md) |
| **Hooks System** | 13 lifecycle hooks and customization | [`docs/hooks.md`](hooks.md) |
| **MCP Integration** | GitHub, Docker, and other MCP servers | [`docs/mcp.md`](mcp.md) |
| **Development** | Contributing and building | [`docs/development.md`](development.md) |

---

## Features

- **Multi-Provider Routing** - Seamlessly switch between Ollama, Claude, Gemini, Codex, and Hugging Face
- **Multi-Model Agent Assignment** - Assign 5+ models from mixed providers to agent types (code, review, test, plan, docs)
- **Auto-Compact Context** - Automatic context management at 85% threshold
- **13 Lifecycle Hooks** - Full hook system: Setup, SessionStart/End, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, SkillTrigger, PreCompact, Stop, SubagentStart/Stop, Notification
- **Skill→Hook→.py Pipeline** - Skills trigger hooks, hooks trigger Python scripts for extensible automation
- **MCP Integration** - Connect to GitHub MCP, Docker MCP, filesystem MCP, and memory MCP servers
- **Status Lines** - Real-time token usage and provider health with job status (idle/thinking/compacting/planning/building)
- **Interactive REPL** - Full chat mode with streaming responses and persistent bottom status bar
- **Token Tracking** - Token usage and cost estimation across providers
- **Session Persistence** - Save and resume conversations
- **RDMA Acceleration** - High-performance networking support (MLX, EXO, RDMA)

---

## Terminal Layout

The interactive REPL uses a three-zone terminal layout:

| Zone | Content |
|------|---------|
| **TOP** | ASCII banner + startup info + warnings (only on startup) |
| **MID** | Prompt region (user input and model responses) |
| **BOTTOM** | Persistent status bar: `cwd │ session-uuid │ model │ context% │ tokens-left │ cost │ job-status` |

The bottom status bar remains visible after every response, so even when the banner scrolls off, you always have context about what the CLI is doing.

---

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/muah1987/ollama-cli/issues)
- **Documentation**: [Full documentation](https://github.com/muah1987/ollama-cli/docs)
- **Ollama**: [Official Ollama website](https://ollama.ai)

---

## License

MIT License - see [LICENSE](../LICENSE) for details.
