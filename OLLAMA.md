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


<!-- session:600ca220c1bb -->
### Session 600ca220c1bb
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 886 (prompt: 878, completion: 8)


<!-- session:7e556b680870 -->
### Session 7e556b680870
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 925 (prompt: 917, completion: 8)


<!-- session:11a1415fc44e -->
### Session 11a1415fc44e
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 964 (prompt: 956, completion: 8)
