# Roadmap

Development plan for bringing Qarin CLI from v0.1 to a production-grade agentic coding assistant with chained sub-agent orchestration.

---

## Architecture Overview

Qarin's orchestration is built on a **Chain Controller** that runs sub-agents in parallel fan-out waves. Each wave spawns multiple agents concurrently, collects their outputs, merges them into a **Shared State**, and passes that state to the next wave.

```
User Prompt (MID)
  │
  ▼
Wave 0: Ingest ─── Primary restates, extracts constraints, initializes SharedState
  │                 Render TOP (banner + warnings) and BOTTOM (cwd + uuid + model)
  ▼
Wave 1: Analysis Fan-out
  ├── Analyzer-A (technical/architectural angle)
  └── Analyzer-B (UX/risk/edge-case angle)
  │   ── Merge 1 → SharedState v1
  ▼
Wave 2: Plan / Validate / Optimize Fan-out
  ├── Planner (step-by-step plan + deliverables)
  ├── Validator (gaps, risks, readiness score 0-100)
  └── Optimizer (simplifications, modularity, performance)
  │   ── Merge 2 → SharedState v2
  ▼
Wave 3: Execution Fan-out
  ├── Executor-1 (concrete outputs: specs, code, config)
  └── Executor-2 (complementary outputs or alternate approach)
  │   ── Merge 3 → SharedState v3
  ▼
Wave 4: Finalization Fan-out
  ├── Monitor (verify against success criteria)
  ├── Reporter (produce user-facing answer for MID)
  └── Cleaner (polish formatting, remove noise)
  │   ── Final Merge → Deliver answer
  ▼
Update BOTTOM (timings + tokens + uuid + exit status)
```

### Shared State

Flows between all waves. Updated deterministically after each merge.

```
SharedState {
  problem_statement       // restated from user prompt
  success_criteria        // how to know we're done
  constraints             // explicit + inferred
  assumptions             // tagged by source agent
  risks                   // accumulated across waves
  plan                    // current plan (updated by Planner, refined by Optimizer)
  artifacts_to_update     // files, configs, schemas to produce
  final_answer_outline    // skeleton filled in by Reporter
}
```

### Sub-agent Contracts

Every sub-agent must return its required fields. Contracts are enforced with Zod schemas.

| Role | Required Return Fields |
|---|---|
| **Analyzer** | `key_insights`, `constraints_found`, `assumptions`, `risks`, `questions_to_clarify`, `recommendations_for_next_wave` |
| **Planner** | `step_by_step_plan`, `deliverables`, `dependencies/tools_needed`, `acceptance_checks`, `recommendations_for_execution` |
| **Validator** | `contradictions_or_gaps`, `risk_register`, `edge_cases`, `must_not_do`, `readiness_score` (0-100) |
| **Optimizer** | `simplifications`, `modularization_suggestions`, `clarity_improvements`, `performance/maintenance considerations` |
| **Executor** | `concrete_output`, `integration_steps`, `tests_or_checks` |
| **Monitor** | Verification against success criteria, remaining risks |
| **Reporter** | User-facing output formatted for MID region |
| **Cleaner** | Polished formatting, no duplicates, CLI region consistency |

### CLI Regions

| Region | Content |
|---|---|
| **TOP** | ASCII banner + startup info + warnings (from `.qarin/warnings` if present) |
| **MID** | User prompt input + final delivered answer |
| **BOTTOM** | cwd, run_uuid, model/status, live metrics (tokens, latency, cost, exit status) |

### Merge Policy

After each wave, the Chain Controller merges sub-agent outputs:

1. **Deduplicate** repeated points using content hashing
2. **Resolve conflicts** by evidence and constraints; if unresolved, present best option + fallback
3. **Produce structured SharedState update** (not raw concatenation)

### Chain Config

```yaml
# .qarin/settings.json → chain section
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
ui:
  top: banner + startup + warnings_if_exists
  mid: prompt_region + final_answer
  bottom: cwd + run_uuid + model + metrics_optional
```

### Primary Orchestrator Prompt

The Chain Controller operates under these rules:

1. Never answer immediately if the task benefits from multi-perspective work; run the chain
2. Each sub-agent must return its contracted fields
3. Merges are deterministic: dedup, resolve conflicts by evidence, produce clean SharedState
4. Stop when the final answer meets success criteria AND validator risks are addressed or documented
5. If tool execution fails, pivot: produce alternative plan and explain constraints

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
| Sub-agents | 40% | Old sequential 4-wave works but needs full rewrite for chain controller |
| Session manager | 85% | Save/load works, full context restoration incomplete |
| UI components | 100% | StatusBar, ChatView, ProgressTheme, InputArea, CodePanel, DiffViewer |
| Themes | 100% | 5 bilingual Arabic/English themes |
| CLI parsing | 80% | All flags parsed, --print and --output-format not wired |
| Chain controller | 0% | Not yet implemented |
| CLI regions | 0% | TOP/MID/BOTTOM layout not yet implemented |
| Tests | 0% | No test files exist |

**Overall: ~70% of the foundation is built. The chain controller, CLI regions, and production hardening are the major remaining work.**

---

## Phase 1 -- Wire the Gaps (v0.2)

_Goal: Make the existing single-agent path work end-to-end before building the chain._

### 1.1 Agentic Loop Completion

- **Parse tool_use blocks** from Anthropic streaming responses
- **Parse function_call / tool_calls** from OpenAI chat completions
- **Map Ollama tool responses** to the unified tool call format
- **Execute tools** and feed results back into the conversation as tool_result messages
- **Guard against runaway loops** with a configurable max-rounds parameter

### 1.2 Streaming Display

- Pipe streamed chunks directly into ChatView as they arrive
- Show a cursor/caret during active generation
- Handle partial tool-call JSON gracefully (buffer until complete)

### 1.3 CLI Modes

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

## Phase 2 -- Chain Controller Foundation (v0.3)

_Goal: Replace the old sequential sub-agent system with the chained fan-out architecture._

### 2.1 SharedState & Types

Define the data structures that flow between waves.

- Create `types/chain.js` with SharedState interface and per-role contract schemas (Zod)
- Define WaveConfig, AgentContract, MergePolicy types
- Define ChainConfig schema for `.qarin/settings.json`

### 2.2 Chain Controller Core

Build `core/chain.js` -- the Primary Orchestrator that replaces `core/subagents.js`.

- **Wave 0: Ingest** -- restate prompt, extract constraints, define success criteria, initialize SharedState
- **Wave runner** -- generic function that takes a wave config (list of agent roles), spawns them in parallel via Promise.allSettled, collects outputs
- **Merge engine** -- deterministic dedup + conflict resolution; produces clean SharedState update after each wave
- **Wave sequencing** -- run Wave 0 → 1 → 2 → 3 → 4, passing SharedState between each
- **Stop conditions** -- halt when success criteria met AND validator risks addressed; or when all waves complete

### 2.3 Sub-agent Roles

Implement the 10 sub-agent roles with their contract prompts.

| Wave | Agents | Key Output |
|---|---|---|
| 1 | Analyzer-A, Analyzer-B | Insights, constraints, risks from different angles |
| 2 | Planner, Validator, Optimizer | Plan + risk register + simplifications |
| 3 | Executor-1, Executor-2 | Concrete outputs (code, specs, config) |
| 4 | Monitor, Reporter, Cleaner | Verified, formatted, polished answer |

Each agent:
- Receives SharedState + its role prompt
- Returns its contracted fields (validated by Zod)
- Runs on a configurable model/provider (defaults from chain config)

### 2.4 Contract Enforcement

- Validate every sub-agent response against its Zod schema
- On contract violation: retry once with a reminder prompt appended
- On second failure: fill missing fields with `null`, flag in merge output
- Log contract violations for debugging

### 2.5 Merge Engine

- **Content hashing** for dedup across agent outputs
- **Evidence-based conflict resolution** -- when agents disagree, pick the answer backed by more constraints; if tied, present best option + fallback
- **Structured output** -- every merge produces a typed SharedState update, never raw concatenation
- **Merge audit trail** -- record what was deduped, what conflicts were resolved, for transparency

### 2.6 Chain Lifecycle Hooks

Add new hook events so external tools can observe orchestration:

- `ChainStart` -- fired when Wave 0 begins
- `WaveStart` -- fired before each wave's parallel spawn
- `WaveComplete` -- fired after each wave's merge
- `MergeComplete` -- fired with the merge audit trail
- `ChainComplete` -- fired with final SharedState + delivered answer

---

## Phase 3 -- CLI Regions & Intelligence (v0.4)

_Goal: Build the TOP/MID/BOTTOM UI layout and make the agent smarter._

### 3.1 CLI Regions

- **TOP component** -- Ink component rendering ASCII banner, startup info, warnings from `.qarin/warnings`
- **MID region** -- refactor ChatView to serve as MID; prompt input + streamed answer
- **BOTTOM component** -- Ink component showing cwd, run_uuid, model/status, live metrics
- **BOTTOM live updates** -- update in real time as waves complete (tokens, timings, cost, exit status)
- **Region layout manager** -- coordinate TOP/MID/BOTTOM in app.js with overflow handling
- **run_uuid** -- generate a unique ID per invocation, display in BOTTOM, use as cache key

### 3.2 Wave Progress UI

- Show which wave is active and which agents are running (spinner per agent)
- Show merge status after each wave completes
- Display cumulative token count and cost across all waves

### 3.3 Intent Classification -- Tier 2

- When Tier 1 confidence < 0.7, ask the active model to classify intent via structured prompt
- Cache classification results for similar prompts
- Support multi-intent detection for compound requests

### 3.4 Context-Aware Classification

- Factor in last N messages when classifying (a "do it" after planning → code, not unknown)

### 3.5 Smart Context Compaction

- Replace truncation with LLM-based summarization at 85% threshold
- Keep summary as first message for long-term awareness
- Fall back to truncation if summarization call fails

### 3.6 Long-term Memory

- Build `.qarin/memory/` system for persisting facts across sessions
- Embedding pipeline using active provider
- Top-K similarity retrieval injected into system message
- `/memory list`, `/memory search <query>`, `/memory clear` commands

### 3.7 Project Context Evolution

- Append session summaries to QARIN.md at session end (opt-in)
- Parse structured QARIN.md sections and inject selectively based on intent

---

## Phase 4 -- Runners, Hooks & Chain Tuning (v0.5)

_Goal: Make tool execution safe, hooks powerful, and the chain adaptive._

### 4.1 Runner Enhancements

- **Sandboxed execution** -- Docker/nsjail for shell_exec with configurable filesystem mounts
- **Streaming shell output** -- pipe stdout/stderr line-by-line to UI
- **Tool confirmation** -- diff/command preview before destructive operations
- **Working directory tracking** -- display and manage cwd across tool calls

### 4.2 New Tools

| Tool | Purpose |
|---|---|
| `git_diff` | Show staged/unstaged diffs, integrate with DiffViewer |
| `git_commit` | Stage and commit with generated message |
| `code_search` | Semantic AST search via tree-sitter |
| `test_run` | Run project test suite, parse results |
| `lint_check` | Run linter, return structured diagnostics |

### 4.3 Tool Plugin System

- Load custom tools from `.qarin/tools/` (JS/TS modules)
- Validate schemas with Zod at load time
- Inject alongside built-ins

### 4.4 Hook Permissions Gate

- PreToolUse hooks can return `{ allow: false, reason: "..." }` to block tool calls
- Configurable allowlists per tool
- Audit log to `.qarin/audit.log`

### 4.5 Built-in Hook Library

| Hook | Event | Action |
|---|---|---|
| `auto-lint` | PostToolUse (file_write) | Run linter on written file |
| `auto-test` | PostToolUse (file_write) | Run tests if test file modified |
| `commit-guard` | PreToolUse (shell_exec) | Block `git push --force` and `rm -rf /` |
| `token-alert` | Notification | Warn when cost exceeds threshold |

### 4.6 Hook Composition

- Chain hooks: output of one becomes input to the next
- Conditional hooks: fire only if matcher predicate returns true
- `/hooks list` command

### 4.7 Adaptive Wave Execution

- **Intent-based wave selection** -- documentation tasks skip Execution wave; simple code tasks skip Analysis wave
- **Confidence gating** -- if Validator readiness_score > 90, skip to Execution
- **Early termination** -- if Monitor confirms success criteria on first pass, stop immediately

### 4.8 Per-wave Configuration

```jsonc
// .qarin/settings.json
{
  "chain": {
    "waves": [
      {
        "name": "analysis",
        "agents": [
          { "role": "analyzer_a", "model": "claude-haiku", "maxTokens": 2000 },
          { "role": "analyzer_b", "model": "claude-haiku", "maxTokens": 2000 }
        ]
      },
      {
        "name": "plan_validate_optimize",
        "agents": [
          { "role": "planner", "model": "claude-sonnet", "maxTokens": 4000 },
          { "role": "validator", "model": "claude-haiku", "maxTokens": 2000 },
          { "role": "optimizer", "model": "claude-haiku", "maxTokens": 2000 }
        ]
      },
      {
        "name": "execution",
        "agents": [
          { "role": "executor_1", "model": "claude-sonnet", "maxTokens": 8000 },
          { "role": "executor_2", "model": "claude-sonnet", "maxTokens": 8000 }
        ]
      },
      {
        "name": "finalize",
        "agents": [
          { "role": "monitor", "model": "claude-haiku", "maxTokens": 2000 },
          { "role": "reporter", "model": "claude-sonnet", "maxTokens": 4000 },
          { "role": "cleaner", "model": "claude-haiku", "maxTokens": 2000 }
        ]
      }
    ]
  }
}
```

### 4.9 Token Budgets

- Set total token budget for a chain run
- Distribute across waves (e.g. 10% Analysis, 20% Plan, 50% Execution, 20% Finalize)
- Abort and report when budget exceeded
- Display cumulative cost in BOTTOM

### 4.10 Sub-agent Result Caching

- Cache wave outputs keyed by SharedState hash
- Skip completed waves on re-run
- Invalidate when source files change
- `/cache clear` command

---

## Phase 5 -- Production Hardening (v1.0)

_Goal: Ship a stable, tested, distributable release._

### 5.1 Testing

- **Unit tests** -- core modules (agent, models, context, tokens, intent, tools, hooks, chain, session)
- **Chain controller tests** -- wave sequencing, parallel spawn, merge logic, SharedState transitions, contract enforcement
- **Component tests** -- Ink component snapshots including TOP/BOTTOM regions
- **Integration tests** -- full CLI runs against mock LLM server (nock/msw)
- **E2E tests** -- scripted terminal sessions asserting on output
- **CI pipeline** -- GitHub Actions: lint, test, build on every PR

### 5.2 Configuration

- Global config at `~/.config/qarin/config.json`
- Project config at `.qarin/config.json`
- CLI flags override everything
- `qarin config set <key> <value>` command

### 5.3 Observability

- Structured logging via Pino (debug, info, warn, error)
- Log rotation and size limits
- Performance metrics: per-wave latency, per-agent tokens, merge times
- Optional opt-in telemetry

### 5.4 Provider Expansion

| Provider | Priority | Notes |
|---|---|---|
| Groq | High | Fast inference, good for Analyzer/Monitor agents |
| Google Gemini | Medium | Large context windows for Executor agents |
| Mistral | Low | European hosting, open-weight models |
| Local (llama.cpp) | Low | Direct GGUF loading without Ollama |

### 5.5 Distribution

- npm publish with GitHub Actions on tagged releases
- Pre-built binaries via Bun for Linux, macOS, Windows
- Homebrew tap for macOS
- Docker image for CI/server usage
- GitHub Releases with changelogs

### 5.6 Documentation

- API reference for core modules
- Chain controller architecture guide
- Sub-agent contract reference
- Theme authoring guide
- Plugin/tool development guide
- Hook cookbook with examples
- Troubleshooting FAQ

---

## Version Summary

| Version | Codename | Focus | Key Deliverable |
|---|---|---|---|
| **v0.2** | Wire the Gaps | Agentic loop, streaming, CLI modes | Tools execute from LLM responses |
| **v0.3** | Chain Controller | SharedState, wave runner, merge engine, contracts | Parallel fan-out orchestration replaces old sequential model |
| **v0.4** | Intelligence & UI | CLI regions, intent Tier 2, memory, smart compaction | TOP/MID/BOTTOM layout + agent remembers across sessions |
| **v0.5** | Runners & Hooks | Sandboxing, new tools, plugins, adaptive waves, budgets | Safe tool execution + cost-controlled chain runs |
| **v1.0** | Production | Tests, CI, distribution, docs | Stable public release |
