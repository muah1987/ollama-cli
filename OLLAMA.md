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


<!-- session:876577732d87 -->
### Session 876577732d87
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 962 (prompt: 954, completion: 8)


<!-- session:71dc4642b4f9 -->
### Session 71dc4642b4f9
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,001 (prompt: 993, completion: 8)


<!-- session:10034d32192b -->
### Session 10034d32192b
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,040 (prompt: 1,032, completion: 8)


<!-- session:86e443a14e74 -->
### Session 86e443a14e74
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,080 (prompt: 1,072, completion: 8)


<!-- session:9ad07ee34b6f -->
### Session 9ad07ee34b6f
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,120 (prompt: 1,112, completion: 8)


<!-- session:8b0ab7abb15c -->
### Session 8b0ab7abb15c
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,160 (prompt: 1,152, completion: 8)


<!-- session:93eaee8bfa4e -->
### Session 93eaee8bfa4e
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,200 (prompt: 1,192, completion: 8)


<!-- session:678dda8feb24 -->
### Session 678dda8feb24
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,240 (prompt: 1,232, completion: 8)


<!-- session:eae322224381 -->
### Session eae322224381
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,280 (prompt: 1,272, completion: 8)


<!-- session:de462ead774d -->
### Session de462ead774d
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,320 (prompt: 1,312, completion: 8)


<!-- session:ee21c25577dd -->
### Session ee21c25577dd
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,360 (prompt: 1,352, completion: 8)


<!-- session:7ec03e97a718 -->
### Session 7ec03e97a718
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,400 (prompt: 1,392, completion: 8)


<!-- session:506a0881dde0 -->
### Session 506a0881dde0
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,440 (prompt: 1,432, completion: 8)


<!-- session:4d93a955d74b -->
### Session 4d93a955d74b
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,480 (prompt: 1,472, completion: 8)


<!-- session:fa7f60ca08b5 -->
### Session fa7f60ca08b5
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,520 (prompt: 1,512, completion: 8)


<!-- session:873b516a983c -->
### Session 873b516a983c
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,560 (prompt: 1,552, completion: 8)


<!-- session:b39a4403fce2 -->
### Session b39a4403fce2
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,600 (prompt: 1,592, completion: 8)


<!-- session:31b92e0679c9 -->
### Session 31b92e0679c9
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,640 (prompt: 1,632, completion: 8)


<!-- session:b1a02880e88e -->
### Session b1a02880e88e
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,680 (prompt: 1,672, completion: 8)


<!-- session:7ccd1b12d255 -->
### Session 7ccd1b12d255
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,720 (prompt: 1,712, completion: 8)


<!-- session:67bbe9159578 -->
### Session 67bbe9159578
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,760 (prompt: 1,752, completion: 8)


<!-- session:e168ea8dd3c2 -->
### Session e168ea8dd3c2
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,800 (prompt: 1,792, completion: 8)


<!-- session:ed744463999f -->
### Session ed744463999f
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,840 (prompt: 1,832, completion: 8)


<!-- session:7103c82c97f8 -->
### Session 7103c82c97f8
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,880 (prompt: 1,872, completion: 8)


<!-- session:3707a7900dec -->
### Session 3707a7900dec
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,920 (prompt: 1,912, completion: 8)


<!-- session:382de991612f -->
### Session 382de991612f
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,960 (prompt: 1,952, completion: 8)


<!-- session:054247c62462 -->
### Session 054247c62462
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 2,000 (prompt: 1,992, completion: 8)
