# Ollama CLI — Project Memory

> This file serves as persistent project memory across sessions, similar to CLAUDE.md.
> The session_end hook automatically appends session summaries below.

## Project Overview

Ollama CLI is a full-featured AI coding assistant powered by Ollama with multi-provider support (Claude, Gemini, Codex). Built using the GOTCHA Framework and ATLAS Workflow from the ai-code-hooks ecosystem.

## Architecture

- **GOTCHA Framework**: Goals, Orchestration, Tools, Context, Hard prompts, Args
- **ATLAS Workflow**: Architect, Trace, Link, Assemble, Stress-test
- **Multi-Provider Routing**: Ollama (local/cloud), Claude, Gemini, Codex
- **Auto-Compact Context**: Automatic compaction at 85% context usage
- **Hook System**: 7 lifecycle hooks mirroring Claude Code

## Configuration

- Default model: llama3.2
- Default provider: ollama (local)
- Context length: 4096 (configurable via OLLAMA_CONTEXT_LENGTH)
- Auto-compact: enabled at 85% threshold
- Hooks: enabled by default

## Source Structure

```
ollama-cli/
├── src/
│   ├── cli.py              — Main CLI entry point (9 commands)
│   ├── api_client.py       — Ollama API client (native + OpenAI-compatible)
│   ├── provider_router.py  — Multi-provider routing (Ollama/Claude/Gemini/Codex)
│   ├── context_manager.py  — Auto-compact context management
│   ├── token_counter.py    — Token tracking with cost estimation
│   ├── session.py          — Session state management
│   ├── config.py           — Configuration management
│   └── hook_runner.py      — Hook execution engine
├── .ollama/
│   ├── settings.json       — Hook configuration
│   ├── hooks/              — 7 lifecycle hook scripts
│   ├── status_lines/       — 3 status line scripts + utils
│   └── memory/             — Persistent session data
├── production/             — GitHub release artifacts
├── OLLAMA.md              — This file (project memory)
├── .env.sample            — Environment variable template
└── pyproject.toml         — Python project configuration
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_HOST | http://localhost:11434 | Ollama server URL |
| OLLAMA_MODEL | llama3.2 | Default model |
| OLLAMA_CONTEXT_LENGTH | 4096 | Context window size |
| OLLAMA_CLI_PROVIDER | ollama | Default provider |
| ANTHROPIC_API_KEY | - | For Claude provider |
| GEMINI_API_KEY | - | For Gemini provider |
| OPENAI_API_KEY | - | For Codex provider |

## Learned Patterns

<!-- Auto-updated by session_end hook -->

## Session History

<!-- Auto-updated by session_end hook -->

---
*Last updated: 2026-02-07*


<!-- session:10e04f9f7ea4 -->
### Session 10e04f9f7ea4
- Model: codellama (claude)
- Duration: 0s
- Messages: 0
- Tokens: 0 (prompt: 0, completion: 0)


<!-- session:eb567ef4f5ad -->
### Session eb567ef4f5ad
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 728 (prompt: 720, completion: 8)


<!-- session:c67adcf04a0c -->
### Session c67adcf04a0c
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 767 (prompt: 759, completion: 8)


<!-- session:63c005dce269 -->
### Session 63c005dce269
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 806 (prompt: 798, completion: 8)


<!-- session:28d9a5d933a2 -->
### Session 28d9a5d933a2
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 845 (prompt: 837, completion: 8)


<!-- session:e651a319f813 -->
### Session e651a319f813
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 884 (prompt: 876, completion: 8)


<!-- session:32e7d91339fa -->
### Session 32e7d91339fa
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 923 (prompt: 915, completion: 8)
