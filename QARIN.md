# Qarin CLI — Project Memory

> This file serves as persistent project memory across sessions, similar to CLAUDE.md.
> The session_end hook automatically appends session summaries below.

## Project Overview

Qarin CLI (v0.1.0) is a TypeScript port of ollama-cli — a full-featured AI coding assistant with multi-provider support (Anthropic Claude, OpenAI, Ollama). Built with Bun/Node.js, React + Ink for terminal UI, and Arabic-themed progress indicators.

## Architecture

- **Runtime**: TypeScript on Bun / Node.js 18+
- **UI**: React + Ink terminal interface with themed progress
- **Multi-Provider Routing**: Anthropic (Claude), OpenAI (GPT), Ollama (local)
- **Auto-Compact Context**: Automatic compaction at 85% of 128K context window
- **Hook System**: 13 lifecycle hooks (SessionStart, PreToolUse, PostToolUse, etc.)
- **Sub-Agent Orchestration**: 4-wave delegation (Diagnostic, Analysis, Solution, Verification)
- **Arabic Themes**: Shisha, Caravan, Qahwa, Scholarly progress indicators

## Configuration

- Default model: claude-sonnet-4-20250514
- Default provider: anthropic
- Context length: 128,000 tokens (configurable)
- Auto-compact: enabled at 85% threshold
- Hooks: enabled by default
- Default theme: shisha

## Source Structure

```
qarin-cli/
├── src/                              — TypeScript source (v0.1.0)
│   ├── index.tsx                     — CLI entry (Commander + Ink)
│   ├── app.tsx                       — Main Ink React app
│   ├── core/
│   │   ├── agent.ts                  — QarinAgent with EventEmitter
│   │   ├── context.ts                — Context manager with auto-compaction
│   │   ├── models.ts                 — Multi-provider LLM abstraction
│   │   ├── tools.ts                  — File ops, shell exec, grep, web fetch
│   │   ├── intent.ts                 — Intent classifier (Tier 1 patterns)
│   │   ├── tokens.ts                 — Token counter with cost estimation
│   │   ├── session.ts                — Session persistence + QARIN.md integration
│   │   ├── hooks.ts                  — Lifecycle hook runner (13 events)
│   │   └── subagents.ts              — 4-wave sub-agent orchestration
│   ├── components/
│   │   ├── StatusBar.tsx             — Session/model/token status bar
│   │   ├── ChatView.tsx              — Message display
│   │   ├── InputArea.tsx             — User input with command handling
│   │   ├── ProgressTheme.tsx         — Arabic-themed progress indicator
│   │   ├── CodePanel.tsx             — Syntax-highlighted code display
│   │   └── DiffViewer.tsx            — Git diff visualization
│   ├── hooks/
│   │   ├── useAgent.ts               — Agent lifecycle React hook
│   │   ├── useTheme.ts               — Theme switching hook
│   │   └── useSubagents.ts           — Sub-agent orchestration hook
│   ├── themes/
│   │   ├── base.ts, shisha.ts        — Base + Shisha (default) themes
│   │   ├── caravan.ts, qahwa.ts      — Caravan + Qahwa themes
│   │   ├── scholarly.ts              — Islamic scholarship theme
│   │   └── index.ts                  — Theme registry
│   └── types/
│       ├── agent.ts                  — Agent/session/tool types
│       ├── message.ts                — Provider/message/token types
│       └── theme.ts                  — Theme/phase types
├── .qarin/
│   ├── settings.json                 — Hook configuration
│   ├── hooks/                        — Lifecycle hook scripts
│   ├── mcp.json                      — MCP server definitions
│   └── chain.json                    — Chain orchestration config
├── package.json                      — v0.1.0 TypeScript package
├── tsconfig.json                     — TypeScript configuration
├── QARIN.md                          — This file (project memory)
└── .env.sample                       — Environment variable template
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| ANTHROPIC_API_KEY | - | For Anthropic Claude provider |
| OPENAI_API_KEY | - | For OpenAI GPT provider |
| OLLAMA_HOST | http://localhost:11434 | Ollama server URL |

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


<!-- session:ffbccfd6fcc6 -->
### Session ffbccfd6fcc6
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,887 (prompt: 1,879, completion: 8)


<!-- session:bc47c83bee33 -->
### Session bc47c83bee33
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,928 (prompt: 1,920, completion: 8)


<!-- session:1333d7bb3554 -->
### Session 1333d7bb3554
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 1,968 (prompt: 1,960, completion: 8)


<!-- session:0c2f71f9d194 -->
### Session 0c2f71f9d194
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 2,008 (prompt: 2,000, completion: 8)


<!-- session:cb05918bfcc1 -->
### Session cb05918bfcc1
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 2,048 (prompt: 2,040, completion: 8)


<!-- session:57bc70a78c6c -->
### Session 57bc70a78c6c
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 2,088 (prompt: 2,080, completion: 8)


<!-- session:1d27f4be47ff -->
### Session 1d27f4be47ff
- Model: llama3.2 (ollama)
- Duration: 3s
- Messages: 1
- Tokens: 2,128 (prompt: 2,120, completion: 8)


<!-- session:summary-test -->
### Session summary-test
- Model: gpt-4 (openai)
- Duration: 1m 0s
- Messages: 5
- Tokens: 750 (prompt: 500, completion: 250)
