# TODO

Current task tracker for Qarin CLI development. Items are grouped by system and ordered by priority within each group.

---

## Agent Core

- [ ] **Tool call extraction** -- parse tool_use blocks from Anthropic responses and function_call from OpenAI responses so the agentic loop can actually invoke tools
- [ ] **Real-time streaming display** -- pipe streamed chunks into ChatView as they arrive instead of waiting for the full response
- [ ] **Retry with exponential backoff** -- detect rate-limit (429) and transient errors, retry up to 4 times with 2s/4s/8s/16s delays
- [ ] **Max tool-call depth guard** -- enforce a configurable ceiling on consecutive tool rounds to prevent runaway loops (currently hard-coded)
- [ ] **Graceful cancellation** -- let the user press Ctrl-C mid-generation to abort the current request without killing the process

## Intelligence / Intent Classification

- [ ] **Tier 2 LLM fallback** -- when Tier 1 pattern confidence < 0.7, send the prompt to the active model for intent classification instead of defaulting to "code"
- [ ] **Dynamic intent registry** -- allow plugins and QARIN.md to register custom intents with their own pattern sets
- [ ] **Multi-intent detection** -- support prompts that span two intents (e.g. "write tests and review the auth module") by returning ranked intent list
- [ ] **Context-aware classification** -- factor in recent conversation history, not just the current prompt, when classifying intent

## Runners / Tool Execution

- [ ] **Sandboxed shell_exec** -- run commands in a restricted environment (cgroups, nsjail, or Docker) to limit blast radius
- [ ] **Streaming shell output** -- pipe long-running command output back to the UI in real time instead of waiting for exit
- [ ] **Tool confirmation prompt** -- ask the user before executing destructive tools (file_write, file_edit, shell_exec) with a configurable allowlist
- [ ] **Tool timeout configuration** -- make per-tool timeouts configurable via settings.json (currently 30s shell, 15s fetch)
- [ ] **New tool: git_diff** -- first-class git diff/status/commit tool that integrates with DiffViewer
- [ ] **New tool: code_search** -- semantic code search using tree-sitter AST queries instead of plain grep

## Hooks System

- [ ] **Permission enforcement** -- hook matchers should be able to block or modify tool calls before execution (PreToolUse gate)
- [ ] **Async hook execution** -- run hooks concurrently where ordering does not matter
- [ ] **Hook error reporting** -- surface hook stderr/failures in the UI instead of silently swallowing them
- [ ] **Built-in hooks library** -- ship default hooks for common workflows (auto-lint on file_write, auto-test on code change)
- [ ] **Hook dry-run mode** -- preview what hooks would fire for a given action without executing them

## Sub-agents

- [ ] **Configurable sub-agent models** -- allow each wave to use a different model/provider via settings.json or CLI flags
- [ ] **Custom wave prompts** -- let QARIN.md override the default system prompts for Diagnostic, Analysis, Solution, Verification agents
- [ ] **Wave skip logic** -- skip unnecessary waves (e.g. skip Verification for documentation tasks)
- [ ] **Parallel wave execution** -- run independent waves concurrently when their inputs don't depend on prior outputs
- [ ] **Sub-agent token budgets** -- enforce per-wave token limits to control cost in multi-agent runs
- [ ] **Sub-agent result caching** -- cache wave outputs so re-running the same task doesn't repeat completed waves

## Session & Context

- [ ] **Full context restoration on resume** -- restore system message, compaction state, and token counters (currently only restores messages)
- [ ] **LLM-based compaction** -- summarise old messages with the active model instead of truncating them
- [ ] **Sliding window strategy** -- offer an alternative compaction mode that keeps a rolling window of N messages
- [ ] **Session export** -- export conversation to Markdown, JSON, or PDF
- [ ] **Session search** -- search across saved sessions by keyword or date
- [ ] **Auto-save interval** -- periodically save the session to prevent data loss on crash

## Long-term Memory

- [ ] **Memory store implementation** -- build the `.qarin/memory/` system for persisting facts across sessions
- [ ] **Embedding pipeline** -- generate embeddings for stored facts using the active provider
- [ ] **Similarity retrieval** -- inject relevant memories into context at session start and before each prompt
- [ ] **Memory management CLI** -- commands to list, search, and delete stored memories

## UI / Components

- [ ] **Syntax highlighting** -- add language-aware coloring to CodePanel (chalk + a highlight grammar)
- [ ] **Multi-file diff view** -- extend DiffViewer to show changes across multiple files in one view
- [ ] **Scrollable chat history** -- allow scrolling through long conversations in the terminal
- [ ] **Notification toasts** -- show brief non-blocking notifications for background events (hook results, sub-agent completions)
- [ ] **Accessibility** -- ensure all UI elements work with screen readers and high-contrast terminals

## CLI & Configuration

- [ ] **Implement --print mode** -- non-interactive mode that streams output to stdout and exits
- [ ] **Implement --output-format** -- apply text/json/markdown formatting to output (flag is parsed but unused)
- [ ] **Global config file** -- support `~/.config/qarin/config.json` for default model, provider, theme, and other settings
- [ ] **Model discovery** -- `qarin models` command to list available models for the active provider
- [ ] **Provider validation** -- verify API key and connectivity on startup, show clear error if missing

## Testing

- [ ] **Unit tests for core/** -- agent, models, context, tokens, intent, tools, hooks, subagents, session
- [ ] **Component tests** -- snapshot or integration tests for Ink components
- [ ] **E2E test harness** -- run the CLI against a mock LLM server and assert on output
- [ ] **CI pipeline** -- GitHub Actions workflow for lint, test, build on every PR

## Providers

- [ ] **Groq provider** -- add Groq API support for fast inference
- [ ] **Google Gemini provider** -- add Gemini API support
- [ ] **Provider health check** -- test provider connectivity on startup and warn if unreachable
- [ ] **Automatic provider fallback** -- if the primary provider fails, fall back to the next in the chain

## Build & Distribution

- [ ] **Test binary build** -- verify `npm run build:binary` produces a working standalone binary
- [ ] **Pre-built binaries** -- publish binaries for Linux, macOS, Windows via GitHub Releases
- [ ] **npm publish automation** -- CI step to publish to npm on tagged releases
- [ ] **Homebrew formula** -- create a Homebrew tap for macOS installation
