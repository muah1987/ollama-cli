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

## Chain Controller (Primary Orchestrator)

The chain controller replaces the old sequential 4-wave model (Diagnostic → Analysis → Solution → Verification) with a parallel fan-out architecture. Each wave spawns multiple sub-agents concurrently, merges their outputs into a Shared State, then passes that state to the next wave.

### Shared State Object

- [ ] **Define SharedState type** -- create `types/chain.js` with the SharedState interface: `problem_statement`, `success_criteria`, `constraints`, `assumptions`, `risks`, `plan`, `artifacts_to_update`, `final_answer_outline`
- [ ] **SharedState lifecycle** -- initialize at Wave 0, update deterministically after each wave merge, serialize for caching/resume
- [ ] **SharedState persistence** -- save/restore SharedState to `.qarin/sessions/` so chain runs can be resumed mid-wave

### Wave 0: Ingest

- [ ] **Restate and extract** -- Primary restates user request in 1-2 lines, extracts explicit + inferred constraints, defines success criteria
- [ ] **Initialize SharedState** -- populate `problem_statement`, `success_criteria`, `constraints` from the ingested prompt
- [ ] **Render TOP region** -- ASCII banner + startup info + warnings (if `.qarin/warnings` file exists)
- [ ] **Render BOTTOM region** -- cwd, run_uuid, model/status, and optional metrics (cpu/gpu/tokens/latency)

### Wave 1: Analysis Fan-out

- [ ] **Analyzer-A sub-agent** -- interprets requirements from a technical/architectural angle; returns `key_insights`, `constraints_found`, `assumptions`, `risks`, `questions_to_clarify`, `recommendations_for_next_wave`
- [ ] **Analyzer-B sub-agent** -- interprets requirements from a UX/risk/edge-case angle; same return contract
- [ ] **Parallel spawn** -- run Analyzer-A and Analyzer-B concurrently via Promise.allSettled
- [ ] **Merge 1** -- deduplicate insights, resolve conflicts by evidence, produce SharedState v1

### Wave 2: Plan / Validate / Optimize Fan-out

- [ ] **Planner sub-agent** -- produces `step_by_step_plan`, `deliverables`, `dependencies/tools_needed`, `acceptance_checks`, `recommendations_for_execution`
- [ ] **Validator sub-agent** -- checks completeness, contradictions, safety/constraints; returns `contradictions_or_gaps`, `risk_register`, `edge_cases`, `must_not_do`, `readiness_score` (0-100)
- [ ] **Optimizer sub-agent** -- returns `simplifications`, `modularization_suggestions`, `clarity_improvements`, `performance/maintenance considerations`
- [ ] **Parallel spawn** -- run Planner, Validator, Optimizer concurrently
- [ ] **Merge 2** -- integrate plan with validator risks and optimizer suggestions, produce SharedState v2

### Wave 3: Execution Fan-out

- [ ] **Executor-1 sub-agent** -- produces concrete outputs (specs, code, config); returns `concrete_output`, `integration_steps`, `tests_or_checks`
- [ ] **Executor-2 sub-agent** -- produces complementary outputs (alternative approach or second file set); same return contract
- [ ] **Tool call delegation** -- Executors can propose tool calls (file_write, shell_exec, etc.) but do not invent tool results
- [ ] **Parallel spawn** -- run Executor-1 and Executor-2 concurrently
- [ ] **Merge 3** -- combine executor outputs, resolve overlapping file edits, produce SharedState v3

### Wave 4: Finalization Fan-out

- [ ] **Monitor sub-agent** -- verify final outputs against success criteria from SharedState; list remaining risks
- [ ] **Reporter sub-agent** -- produce the user-facing response formatted for MID region
- [ ] **Cleaner sub-agent** -- polish formatting, remove noise/duplicates, ensure consistency with CLI regions (TOP/MID/BOTTOM)
- [ ] **Parallel spawn** -- run Monitor, Reporter, Cleaner concurrently
- [ ] **Final Merge** -- assemble the delivered answer; update BOTTOM with timings, tokens, uuid, exit status

### Merge Engine

- [ ] **Deterministic dedup** -- deduplicate repeated points across sub-agent outputs using content hashing
- [ ] **Conflict resolution** -- when sub-agents disagree, resolve by evidence/constraints; if unresolved, present best option + fallback
- [ ] **Structured merge output** -- every merge produces a clean SharedState update, not raw concatenation

### Chain Config

- [ ] **Chain config schema** -- define the chain configuration format in `.qarin/settings.json` under a `chain` key
- [ ] **Per-wave agent list** -- configure which agents run in each wave, what model/provider/maxTokens each uses
- [ ] **Merge policy** -- configurable merge strategy per wave (deterministic_dedup_conflict_resolve, or custom)
- [ ] **Wave skip rules** -- configure which waves to skip based on intent or SharedState readiness_score

```yaml
# Target config shape
chain:
  merge_policy: deterministic_dedup_conflict_resolve
  waves:
    - name: analysis
      agents: [analyzer_a, analyzer_b]
    - name: plan_validate_optimize
      agents: [planner, validator, optimizer]
    - name: execution
      agents: [executor_1, executor_2]
    - name: finalize
      agents: [monitor, reporter, cleaner]
```

### Sub-agent Contracts

- [ ] **Enforce return contracts** -- validate that each sub-agent returns its required fields (e.g. Analyzer must return `key_insights`, `risks`, etc.) using Zod schemas
- [ ] **Contract violation handling** -- if a sub-agent omits required fields, retry once with a reminder prompt; if it fails again, fill with `null` and flag in the merge
- [ ] **Contract documentation** -- generate contract docs from the Zod schemas for each role

## CLI UI Regions (TOP / MID / BOTTOM)

- [ ] **TOP region component** -- new Ink component that renders ASCII banner, startup info, and warnings from `.qarin/warnings` file
- [ ] **MID region** -- refactor ChatView to be the MID region; user prompt input + final answer output
- [ ] **BOTTOM region component** -- new Ink component showing cwd, run_uuid, model/status, and live metrics (tokens, latency, cost)
- [ ] **BOTTOM live updates** -- update BOTTOM in real time as waves complete (timings, token counts, exit status)
- [ ] **Region layout manager** -- coordinate TOP/MID/BOTTOM rendering in app.js with proper spacing and overflow handling

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
- [ ] **Chain lifecycle hooks** -- new hook events: `ChainStart`, `WaveStart`, `WaveComplete`, `MergeComplete`, `ChainComplete` so external tools can observe orchestration

## Session & Context

- [ ] **Full context restoration on resume** -- restore system message, compaction state, and token counters (currently only restores messages)
- [ ] **LLM-based compaction** -- summarise old messages with the active model instead of truncating them
- [ ] **Sliding window strategy** -- offer an alternative compaction mode that keeps a rolling window of N messages
- [ ] **Session export** -- export conversation to Markdown, JSON, or PDF
- [ ] **Session search** -- search across saved sessions by keyword or date
- [ ] **Auto-save interval** -- periodically save the session to prevent data loss on crash
- [ ] **Chain run metadata** -- save chain run UUID, wave timings, and per-agent token usage in session data

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
- [ ] **Wave progress indicator** -- show which wave is active, which agents are running, and a live merge status during chain runs
- [ ] **Accessibility** -- ensure all UI elements work with screen readers and high-contrast terminals

## CLI & Configuration

- [ ] **Implement --print mode** -- non-interactive mode that streams output to stdout and exits
- [ ] **Implement --output-format** -- apply text/json/markdown formatting to output (flag is parsed but unused)
- [ ] **Global config file** -- support `~/.config/qarin/config.json` for default model, provider, theme, and other settings
- [ ] **Model discovery** -- `qarin models` command to list available models for the active provider
- [ ] **Provider validation** -- verify API key and connectivity on startup, show clear error if missing
- [ ] **--chain flag** -- explicitly enable chain orchestration mode (vs single-agent mode) from the CLI
- [ ] **run_uuid generation** -- generate a unique run ID per invocation, display in BOTTOM, use as cache/session key

## Testing

- [ ] **Unit tests for core/** -- agent, models, context, tokens, intent, tools, hooks, subagents, session
- [ ] **Chain controller tests** -- test wave sequencing, parallel spawn, merge logic, SharedState transitions
- [ ] **Sub-agent contract tests** -- verify each role returns its required fields against Zod schemas
- [ ] **Component tests** -- snapshot or integration tests for Ink components (including TOP/BOTTOM regions)
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
