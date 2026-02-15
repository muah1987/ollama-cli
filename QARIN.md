# Qarin CLI — Project Memory

> This file serves as persistent project memory across sessions, similar to CLAUDE.md.
> The session_end hook automatically appends session summaries below.

## Project Overview

Qarin CLI is a full-featured AI coding assistant powered by Ollama with multi-provider support (Claude, Gemini, Codex). Built using the GOTCHA Framework and ATLAS Workflow from the ai-code-hooks ecosystem.

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
qarin-cli/
├── src/
│   ├── cli.py              — Main CLI entry point (9 commands)
│   ├── api_client.py       — Ollama API client (native + OpenAI-compatible)
│   ├── provider_router.py  — Multi-provider routing (Ollama/Claude/Gemini/Codex)
│   ├── context_manager.py  — Auto-compact context management
│   ├── token_counter.py    — Token tracking with cost estimation
│   ├── session.py          — Session state management
│   ├── config.py           — Configuration management
│   └── hook_runner.py      — Hook execution engine
├── .qarin/
│   ├── settings.json       — Hook configuration
│   ├── hooks/              — 7 lifecycle hook scripts
│   ├── status_lines/       — 3 status line scripts + utils
│   └── memory/             — Persistent session data
├── production/             — GitHub release artifacts
├── QARIN.md              — This file (project memory)
├── .env.sample            — Environment variable template
└── pyproject.toml         — Python project configuration
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_HOST | http://localhost:11434 | Ollama server URL |
| OLLAMA_MODEL | llama3.2 | Default model |
| OLLAMA_CONTEXT_LENGTH | 4096 | Context window size |
| QARIN_CLI_PROVIDER | ollama | Default provider |
| ANTHROPIC_API_KEY | - | For Claude provider |
| GEMINI_API_KEY | - | For Gemini provider |
| OPENAI_API_KEY | - | For Codex provider |

## Learned Patterns

<!-- Auto-updated by session_end hook -->

## Session History

<!-- Auto-updated by session_end hook -->

---
*Last updated: 2026-02-14*


<!-- session:8080a46c5e41 -->
### Session 8080a46c5e41
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 886 (prompt: 878, completion: 8)


<!-- session:4857afb91e21 -->
### Session 4857afb91e21
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 925 (prompt: 917, completion: 8)


<!-- session:72e54d8f7eeb -->
### Session 72e54d8f7eeb
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 964 (prompt: 956, completion: 8)


<!-- session:b9bf08071a07 -->
### Session b9bf08071a07
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,003 (prompt: 995, completion: 8)


<!-- session:b034820c800e -->
### Session b034820c800e
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,042 (prompt: 1,034, completion: 8)


<!-- session:b646d66a39ed -->
### Session b646d66a39ed
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,082 (prompt: 1,074, completion: 8)


<!-- session:04a5f25d98aa -->
### Session 04a5f25d98aa
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,122 (prompt: 1,114, completion: 8)


<!-- session:b14ec4869fdf -->
### Session b14ec4869fdf
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,162 (prompt: 1,154, completion: 8)


<!-- session:43bccdff61c1 -->
### Session 43bccdff61c1
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,250 (prompt: 1,242, completion: 8)


<!-- session:851493e08e72 -->
### Session 851493e08e72
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,290 (prompt: 1,282, completion: 8)


<!-- session:3d78c9ac1b6e -->
### Session 3d78c9ac1b6e
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,330 (prompt: 1,322, completion: 8)


<!-- session:312270c9a6cd -->
### Session 312270c9a6cd
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,370 (prompt: 1,362, completion: 8)


<!-- session:b9f947d4bc5b -->
### Session b9f947d4bc5b
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,410 (prompt: 1,402, completion: 8)


<!-- session:c3682ca8747c -->
### Session c3682ca8747c
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,450 (prompt: 1,442, completion: 8)


<!-- session:c62a13f4f2c3 -->
### Session c62a13f4f2c3
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,490 (prompt: 1,482, completion: 8)


<!-- session:8dadafdf517f -->
### Session 8dadafdf517f
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,530 (prompt: 1,522, completion: 8)


<!-- session:e5233f02387d -->
### Session e5233f02387d
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,570 (prompt: 1,562, completion: 8)


<!-- session:cfa0536c7456 -->
### Session cfa0536c7456
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,610 (prompt: 1,602, completion: 8)


<!-- session:9d860f7d5492 -->
### Session 9d860f7d5492
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,649 (prompt: 1,641, completion: 8)


<!-- session:fea6415ed241 -->
### Session fea6415ed241
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,689 (prompt: 1,681, completion: 8)


<!-- session:fcfa2a654f60 -->
### Session fcfa2a654f60
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,729 (prompt: 1,721, completion: 8)


<!-- session:7020e6c5b0a5 -->
### Session 7020e6c5b0a5
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,769 (prompt: 1,761, completion: 8)


<!-- session:7c54b282af0a -->
### Session 7c54b282af0a
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,809 (prompt: 1,801, completion: 8)


<!-- session:6d95671770db -->
### Session 6d95671770db
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,847 (prompt: 1,839, completion: 8)
