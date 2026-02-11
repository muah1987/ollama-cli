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
| **CLI Reference** | All available commands | [`docs/cli_reference.md`](cli_reference.md) |
| **API Reference** | Ollama and provider APIs | [`docs/api_reference.md`](api_reference.md) |
| **Configuration** | Environment variables and settings | [`docs/configuration.md`](configuration.md) |
| **Multi-Provider** | Using Claude, Gemini, Codex | [`docs/multi_provider.md`](multi_provider.md) |
| **Agent Models** | Agent-specific model assignments | [`docs/agent_model_assignment.md`](agent_model_assignment.md) |
| **RDMA Support** | High-performance networking | [`docs/rdma.md`](rdma.md) |
| **Hooks System** | Lifecycle hooks and customization | [`docs/hooks.md`](hooks.md) |
| **Development** | Contributing and building | [`docs/development.md`](development.md) |

---

## Features

- **Multi-Provider Routing** - Seamlessly switch between Ollama, Claude, Gemini, and Codex
- **Agent Model Assignment** - Assign specific models to agent types for specialized tasks
- **Auto-Compact Context** - Automatic context management at 85% threshold
- **Hook System** - 7 lifecycle hooks for customization
- **Status Lines** - Real-time token usage and provider health
- **Interactive REPL** - Full chat mode with streaming responses
- **Token Tracking** - Token usage and cost estimation across providers
- **Session Persistence** - Save and resume conversations
- **RDMA Acceleration** - High-performance networking support (MLX, EXO, RMDA)

---

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/muah1987/ollama-cli/issues)
- **Documentation**: [Full documentation](https://github.com/muah1987/ollama-cli/docs)
- **Ollama**: [Official Ollama website](https://ollama.ai)

---

## License

MIT License - see [LICENSE](../LICENSE) for details.
