# Roadmap

Development plan for bringing Qarin CLI from v0.1 to a production-grade agentic coding assistant. The roadmap is split into four phases, each building on the last.

---

## Current State (v0.1.0)

What already works:

| System | Status | Notes |
|---|---|---|
| Agent core | 95% | Event-driven loop, streaming, lifecycle hooks |
| Model providers | 100% | Anthropic, OpenAI, Ollama with streaming |
| Context manager | 95% | Auto-compaction at 85% threshold |
| Token counter | 100% | Real-time tracking with cost estimation |
| Intent classifier | 80% | Tier 1 pattern matching (8 intents), Tier 2 LLM fallback not wired |
| Tools | 100% | All 6 tools implemented (file r/w/edit, shell, grep, fetch) |
| Hook runner | 90% | 13 lifecycle events, subprocess execution, no permission gates |
| Sub-agents | 90% | 4-wave orchestration works, configs are hard-coded |
| Session manager | 85% | Save/load works, full context restoration incomplete |
| UI components | 100% | StatusBar, ChatView, ProgressTheme, InputArea, CodePanel, DiffViewer |
| Themes | 100% | 5 bilingual Arabic/English themes |
| CLI parsing | 80% | All flags parsed, --print and --output-format not wired |
| Tests | 0% | No test files exist |

**Overall: ~85% of the foundation is built. The gaps are in wiring, polish, and production hardening.**

---

## Phase 1 -- Wire the Gaps (v0.2)

_Goal: Make everything that's built actually work end-to-end._

### 1.1 Agentic Loop Completion

The agent has a tool-call loop but the critical piece -- extracting tool calls from provider responses -- is missing. Without it, the agent thinks but never acts.

- **Parse tool_use blocks** from Anthropic streaming responses
- **Parse function_call / tool_calls** from OpenAI chat completions
- **Map Ollama tool responses** to the unified tool call format
- **Execute tools** and feed results back into the conversation as tool_result messages
- **Guard against runaway loops** with a configurable max-rounds parameter

### 1.2 Streaming Display

The agent streams tokens but they aren't rendered until the full response arrives.

- Pipe streamed chunks directly into ChatView as they arrive
- Show a cursor/caret during active generation
- Handle partial tool-call JSON gracefully (buffer until complete)

### 1.3 CLI Modes

Two parsed-but-unused flags need to be connected.

- **--print**: Disable Ink rendering, stream plain text to stdout, exit on completion
- **--output-format**: Format the final output as text, json, or markdown

### 1.4 Error Resilience

- Detect HTTP 429 (rate limit) and 5xx errors from providers
- Retry with exponential backoff (2s, 4s, 8s, 16s)
- Surface clear error messages in the UI when retries are exhausted
- Let Ctrl-C cancel the current generation without killing the process

### 1.5 Session Resume Fix

- Restore full context state on `--resume` (system message, compaction checkpoint, token counters)
- Re-inject QARIN.md context if the project file has changed since the session was saved

---

## Phase 2 -- Intelligence (v0.3)

_Goal: Make the agent smarter about what it does and when._

### 2.1 Intent Classification -- Tier 2

When Tier 1 pattern matching returns low confidence, ask the active model to classify the intent.

- Send a structured prompt: `"Classify the user's intent into one of: code, review, test, debug, plan, docs, research. Respond with JSON."`
- Cache classification results for similar prompts to avoid repeated LLM calls
- Support multi-intent detection for compound requests ("write tests and review auth")

### 2.2 Context-Aware Classification

Factor in the last N messages when classifying. A "do it" after a planning discussion should resolve to "code", not "unknown".

### 2.3 Smart Context Compaction

Replace the current truncation strategy with LLM-based summarization.

- When context hits the 85% threshold, summarize the oldest messages into a compressed "memory" block
- Keep the summary as the first message so the agent retains long-term awareness
- Fall back to truncation if the summarization call fails

### 2.4 Long-term Memory

Build the `.qarin/memory/` system.

- **Store**: Save key facts, decisions, and user preferences as structured entries
- **Embed**: Generate embeddings using the active provider's embedding endpoint
- **Retrieve**: On each new prompt, find the top-K most relevant memories and inject them into the system message
- **Manage**: Add `/memory list`, `/memory search <query>`, `/memory clear` commands

### 2.5 Project Context Evolution

Make QARIN.md a living document.

- Append a session summary to QARIN.md at session end (opt-in)
- Parse structured sections in QARIN.md (## Architecture, ## Conventions, ## Known Issues) and inject them selectively based on intent

---

## Phase 3 -- Agents & Orchestration (v0.4)

_Goal: Make the multi-agent system configurable, efficient, and cost-aware._

### 3.1 Configurable Sub-agents

Remove the hard-coded defaults and let users control the orchestration.

```jsonc
// .qarin/settings.json
{
  "subagents": {
    "diagnostic": { "model": "claude-haiku", "maxTokens": 2000 },
    "analysis":   { "model": "claude-sonnet", "maxTokens": 4000 },
    "solution":   { "model": "claude-sonnet", "maxTokens": 8000 },
    "verification": { "model": "claude-haiku", "maxTokens": 2000 }
  }
}
```

- Per-wave model, provider, max tokens, and system prompt overrides
- QARIN.md sections can override wave prompts (e.g. `## Qarin Diagnostic Prompt`)

### 3.2 Adaptive Wave Execution

Not every task needs all four waves.

- **Intent-based wave selection**: Documentation tasks skip Verification. Simple code tasks skip Diagnostic.
- **Confidence gating**: If Diagnostic returns high confidence, skip Analysis and go straight to Solution.
- **Early termination**: If Solution produces a result that passes Verification on the first try, stop immediately.

### 3.3 Parallel Waves

When waves are independent (e.g. running multiple Diagnostic agents on different files), execute them concurrently.

- Implement a wave dependency graph
- Use Promise.allSettled for concurrent wave execution
- Merge parallel wave outputs before passing to the next stage

### 3.4 Token Budgets

Control cost in multi-agent runs.

- Set a total token budget for an orchestration run
- Distribute budget across waves (e.g. 10% Diagnostic, 20% Analysis, 50% Solution, 20% Verification)
- Abort and report when budget is exceeded
- Display cumulative cost in the UI during orchestration

### 3.5 Sub-agent Result Caching

Cache wave outputs keyed by input hash.

- Skip completed waves when re-running the same task
- Invalidate cache when source files change (use file mtimes or content hashes)
- `/cache clear` command

---

## Phase 4 -- Runners & Hooks (v0.5)

_Goal: Make tool execution safe, extensible, and integrated with developer workflows._

### 4.1 Runner Enhancements

- **Sandboxed execution**: Run shell_exec in a restricted environment (Docker container or nsjail) with configurable filesystem mounts
- **Streaming shell output**: Pipe stdout/stderr back to the UI line-by-line for long-running commands
- **Working directory management**: Track and display the agent's working directory, support `cd` between tool calls
- **Tool confirmation**: Before destructive operations (file_write, shell_exec), show a diff or command preview and ask the user to confirm

### 4.2 New Tools

| Tool | Purpose |
|---|---|
| `git_diff` | Show staged/unstaged diffs, integrate with DiffViewer |
| `git_commit` | Stage and commit with a generated message |
| `code_search` | Semantic AST search via tree-sitter |
| `test_run` | Execute the project's test suite and parse results |
| `lint_check` | Run the project's linter and return structured diagnostics |

### 4.3 Tool Plugin System

Let users register custom tools without modifying core code.

- Load tool definitions from `.qarin/tools/` (JS/TS modules exporting name, description, parameters, execute)
- Validate tool schemas with Zod at load time
- Inject custom tools into the agent's tool list alongside built-ins

### 4.4 Hook Permissions Gate

Turn hooks into a security layer.

- **PreToolUse hooks** can return `{ allow: false, reason: "..." }` to block a tool call
- **Allowlists**: Configure which tools are auto-approved vs require confirmation
- **Audit log**: Write every tool execution (input, output, duration, approval status) to `.qarin/audit.log`

### 4.5 Built-in Hook Library

Ship hooks for common workflows.

| Hook | Event | Action |
|---|---|---|
| `auto-lint` | PostToolUse (file_write) | Run linter on the written file |
| `auto-test` | PostToolUse (file_write) | Run tests if a test file was modified |
| `commit-guard` | PreToolUse (shell_exec) | Block `git push --force` and `rm -rf /` |
| `token-alert` | Notification | Warn when session cost exceeds a threshold |

### 4.6 Hook Composition

- Allow hooks to chain: output of one hook becomes input to the next
- Support conditional hooks: only fire if a matcher predicate returns true
- Add a `/hooks list` command to show active hooks and their configuration

---

## Phase 5 -- Production Hardening (v1.0)

_Goal: Ship a stable, tested, distributable release._

### 5.1 Testing

- **Unit tests**: Core modules (agent, models, context, tokens, intent, tools, hooks, subagents, session)
- **Component tests**: Ink component snapshots with ink-testing-library
- **Integration tests**: Full CLI runs against a mock LLM server (nock/msw)
- **E2E tests**: Scripted terminal sessions asserting on output
- **CI pipeline**: GitHub Actions running lint, test, build on every PR

### 5.2 Configuration

- Global config at `~/.config/qarin/config.json` with defaults for model, provider, theme, token budgets
- Project config at `.qarin/config.json` that overrides globals
- CLI flags override everything
- `qarin config set <key> <value>` command

### 5.3 Observability

- Structured logging with levels (debug, info, warn, error) via Pino
- Log rotation and size limits
- Performance metrics: response latency, tool execution time, tokens/second
- Optional telemetry (opt-in) for usage analytics

### 5.4 Provider Expansion

| Provider | Priority | Notes |
|---|---|---|
| Groq | High | Fast inference, good for sub-agents |
| Google Gemini | Medium | Large context windows |
| Mistral | Low | European hosting, open-weight models |
| Local (llama.cpp) | Low | Direct GGUF loading without Ollama |

### 5.5 Distribution

- npm publish with GitHub Actions on tagged releases
- Pre-built binaries via Bun for Linux, macOS, Windows
- Homebrew tap for macOS
- Docker image for CI/server usage
- GitHub Releases with changelogs

### 5.6 Documentation

- API reference for core modules (generated from JSDoc)
- Theme authoring guide
- Plugin/tool development guide
- Hook cookbook with examples
- Architecture diagram
- Troubleshooting FAQ

---

## Version Summary

| Version | Codename | Focus | Key Deliverable |
|---|---|---|---|
| **v0.2** | Wire the Gaps | Agentic loop, streaming, CLI modes | Tools actually execute from LLM responses |
| **v0.3** | Intelligence | Intent Tier 2, memory, smart compaction | Agent remembers and reasons across sessions |
| **v0.4** | Orchestration | Configurable sub-agents, parallel waves, budgets | Multi-agent runs are fast, cheap, and controllable |
| **v0.5** | Runners & Hooks | Sandboxing, new tools, plugins, permission gates | Safe, extensible tool execution |
| **v1.0** | Production | Tests, CI, distribution, docs | Stable public release |
