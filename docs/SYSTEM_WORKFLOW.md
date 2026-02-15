# Qarin CLI — System Workflow

> Complete end-to-end reference for how every layer of Qarin CLI connects.
> Last updated: 2026-02-14

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Terminal                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   CLI Entry Point   │  qarin_cmd/root.py
                    │   (Arg Parser)      │
                    └──────┬─────────┬────┘
                           │         │
              ┌────────────▼─┐   ┌───▼────────────┐
              │ One-shot Mode│   │ Interactive TUI │  tui/app.py
              │  (--prompt)  │   │  (Textual App)  │
              └──────┬───────┘   └──────┬──────────┘
                     │                  │
                     └────────┬─────────┘
                              │
                    ┌─────────▼──────────┐
                    │      Session       │  model/session.py
                    │  (State Machine)   │
                    └──┬───┬───┬───┬─────┘
                       │   │   │   │
          ┌────────────┘   │   │   └─────────────┐
          │                │   │                  │
   ┌──────▼──────┐  ┌─────▼───▼─────┐  ┌────────▼────────┐
   │   Context   │  │   Provider    │  │   Hook Runner   │
   │   Manager   │  │    Router     │  │   (Lifecycle)   │
   │ (Auto-compact) │  (Fallback)    │  │  server/hook_   │
   │ runner/     │  │  api/provider │  │   runner.py     │
   │ context_    │  │  _router.py   │  └─────────────────┘
   │ manager.py  │  └───┬───┬───┬──┘
   └─────────────┘      │   │   │
        ┌───────────────┘   │   └──────────────┐
        │                   │                  │
  ┌─────▼─────┐   ┌────────▼────────┐  ┌──────▼──────┐
  │  Ollama   │   │ Claude/Gemini/  │  │  Hugging    │
  │  (local)  │   │ Codex (cloud)   │  │    Face     │
  │ api/      │   │ api/provider_   │  │ api/        │
  │ ollama_   │   │ router.py       │  │ provider_   │
  │ client.py │   │ (HTTP clients)  │  │ router.py   │
  └───────────┘   └─────────────────┘  └─────────────┘
```

---

## 1. Entry Point — `qarin_cmd/root.py`

The CLI starts at `main()`:

```
main() → parse_args()
  ├── No args / --interactive  →  cmd_interactive()  →  Launch TUI
  ├── --prompt "message"       →  cmd_run_prompt()   →  One-shot send
  ├── run <prompt>             →  cmd_run_prompt()
  ├── pull <model>             →  cmd_pull()
  ├── show <model>             →  cmd_show()
  ├── init                     →  cmd_init()
  └── ... (other subcommands registered via COMMAND_MAP)
```

**Key behaviour:** When stdin is a pipe, reads input as a one-shot prompt.
Otherwise defaults to interactive TUI mode.

---

## 2. TUI Layer — `tui/app.py`, `tui/screens/chat.py`

```
ChatApp (Textual Application)
  └── mount() → ChatScreen
        ├── BannerWidget      (top: logo + version)
        ├── ChatMessageArea   (middle: scrollable messages)
        ├── InputArea         (bottom: text input)
        └── StatusBar         (bottom: cwd, UUID, model, context%, job)
```

**User input flow:**
1. User types in `InputArea`
2. Input reaches `CommandProcessor.dispatch()`
3. If input starts with `/` → slash command handler
4. If input starts with `@agent` → route to specific agent type
5. Otherwise → `Session.send(message)` → display response

**Keyboard shortcuts:**
| Key | Action |
|-----|--------|
| Ctrl+P | Command palette |
| Ctrl+B | Toggle sidebar |
| Ctrl+S | Save session |
| Ctrl+L | Clear chat |
| F1 | Help |

---

## 3. Command Processor — `tui/command_processor.py`

The `CommandProcessor` dispatches 30+ slash commands across 5 categories:

| Category | Commands |
|----------|----------|
| **Session** | `/status`, `/clear`, `/model`, `/provider`, `/save`, `/load`, `/history` |
| **Memory** | `/compact`, `/memory`, `/remember`, `/recall` |
| **Tools** | `/tools`, `/tool`, `/pull`, `/diff`, `/mcp` |
| **Agents** | `/agents`, `/set-agent-model`, `/list-agent-models`, `/chain`, `/team_planning`, `/build`, `/resume`, `/intent`, `/complete_w_team` |
| **Project** | `/init`, `/config`, `/settings`, `/bug` |
| **Other** | `/help`, `/quit`, `/exit` |

Each command maps to a `_cmd_<name>()` handler method.

---

## 4. Session — `model/session.py`

The `Session` is the central state machine that ties everything together.

```
Session.__init__()
  ├── session_id          (UUID)
  ├── model / provider    (current model config)
  ├── ContextManager      (message history + auto-compact)
  ├── TokenCounter        (usage tracking + cost)
  ├── AgentCommBus        (agent-to-agent messaging)
  ├── MemoryLayer         (persistent facts/preferences)
  └── ProviderRouter      (multi-provider routing)

Session.start()
  ├── Load QARIN.md as system prompt
  ├── Load persistent memory from .qarin/memory.json
  └── Fire SessionStart hook

Session.send(message)
  ├── Add user message to ContextManager
  ├── Fire UserPromptSubmit hook (can deny)
  ├── Route via ProviderRouter.route()
  │     └── Provider.chat(messages, model)
  ├── Record assistant response
  ├── Update TokenCounter
  ├── Check auto-compact threshold (85%)
  │     └── If exceeded → compact()
  ├── Fire Stop hook
  └── Return {content, metrics, compacted}

Session.end()
  ├── Save session state
  ├── Append summary to QARIN.md
  ├── Persist memory to .qarin/memory.json
  └── Fire SessionEnd hook
```

---

## 5. Provider Router — `api/provider_router.py`

Routes requests to the optimal provider with automatic fallback:

```
ProviderRouter.route(task_type, messages, agent_type, model, provider)
  │
  ├── 1. Resolve (provider, model) from:
  │     ├── Explicit provider/model override
  │     ├── Agent-type model map (_AGENT_MODEL_MAP)
  │     └── Task-type config (coding/agent/subagent/embedding)
  │
  ├── 2. Build attempt order:
  │     [primary] + [ollama, claude, gemini, codex, hf] minus primary
  │
  └── 3. Try each provider:
        ├── Get/create cached provider instance
        ├── provider.chat(messages, model)
        ├── On success → return response
        ├── On OllamaModelNotFoundError → auto-select available model
        ├── On ProviderAuthError → skip (no credentials)
        └── On timeout/connection error → try next provider
```

**Providers:**
| Provider | Class | Auth | Base URL |
|----------|-------|------|----------|
| Ollama | `OllamaProvider` | Optional `OLLAMA_API_KEY` | `http://localhost:11434` |
| Claude | `ClaudeProvider` | `ANTHROPIC_API_KEY` | `https://api.anthropic.com` |
| Gemini | `GeminiProvider` | `GEMINI_API_KEY` | `https://generativelanguage.googleapis.com` |
| Codex | `CodexProvider` | `OPENAI_API_KEY` | `https://api.openai.com` |
| HF | `HfProvider` | `HF_TOKEN` | `https://router.huggingface.co/v1` |

---

## 6. Error Hierarchy — `api/errors.py`

All exceptions inherit from a single root for flexible catch handling:

```
CliOllamaError (root)
├── ProviderError
│   ├── ProviderUnavailableError
│   ├── ProviderAuthError
│   ├── ProviderRateLimitError
│   └── ProviderResponseError
├── OllamaError
│   ├── OllamaConnectionError
│   └── OllamaModelNotFoundError
├── ConfigurationError
└── SessionError
```

Every error supports `user_message` (property) and `hint` (keyword arg)
for user-friendly display.

---

## 7. Intent Classifier — `runner/intent_classifier.py`

Two-tier classification maps user prompts to the optimal agent type:

```
User prompt → IntentClassifier.classify()
  ├── Tier 1: Pattern matching (deterministic, fast)
  │     ├── Score each agent type by keyword hits
  │     ├── 2x weight for matches in first 5 words
  │     ├── Tie-break by earliest match position
  │     └── Normalise to [0.0, 1.0] confidence
  │
  └── Tier 2: LLM fallback (when Tier 1 confidence < threshold)
        └── Lightweight model call for semantic classification
```

**Agent types:** `code`, `review`, `test`, `debug`, `plan`, `docs`,
`orchestrator`, `team`, `research`

---

## 8. Context Management — `runner/context_manager.py`

Manages conversation history with automatic compaction:

```
ContextManager
  ├── messages[]              (conversation history)
  ├── max_context_length      (default: 4096 tokens)
  ├── compact_threshold       (default: 0.85 = 85%)
  ├── keep_last_n             (messages to preserve)
  │
  ├── add_message(role, content)
  ├── should_compact()        → bool (usage > threshold?)
  ├── compact()               → summarise old messages
  ├── get_context_usage()     → {used, max, percentage, remaining}
  └── sub_contexts            → parallel agent contexts
```

**Auto-compact trigger:** When `estimated_tokens > 85% × max_context_length`,
older messages are summarised and replaced with a compact summary, keeping
the most recent N messages intact.

---

## 9. Chain Orchestration — `runner/chain_controller.py`

Multi-wave subagent pipeline for complex tasks:

```
ChainController.run_chain(prompt)
  │
  ├── Wave 0: Ingest
  │     ├── Parse prompt
  │     ├── Initialise SharedState
  │     └── Auto-allocate models to agent roles
  │
  ├── Wave 1: Analysis
  │     ├── analyzer_a (technical perspective)
  │     └── analyzer_b (UX/risk perspective)
  │
  ├── Wave 2: Plan / Validate / Optimise
  │     ├── planner     → step-by-step plan
  │     ├── validator   → risk register, readiness score
  │     └── optimizer   → simplifications, modularisation
  │
  ├── Wave 3: Execution
  │     ├── executor_1  → concrete output (code/config)
  │     └── executor_2  → concrete output (tests/docs)
  │
  ├── Wave 4: Finalise
  │     ├── monitor     → verify against success criteria
  │     ├── reporter    → user-facing final output
  │     └── cleaner     → polish formatting, remove noise
  │
  └── Deliver → {run_id, final_output, shared_state, wave_results}
```

**SharedState** carries context across waves: `problem_statement`,
`constraints`, `assumptions`, `risks`, `plan`, `artifacts`,
`success_criteria`.

**Merge policy:** Deterministic dedup with keyword-based classification
into shared state fields.

---

## 10. Team Completion Loop — `runner/team_completion.py`

Lighter agentic loop invoked via `/complete_w_team`:

```
TeamCompletionLoop.run(task_description)
  │
  ├── Phase 1: Analyse   → analyst examines task
  ├── Phase 2: Plan      → planner creates implementation plan
  ├── Phase 3: Validate  → validator reviews plan for gaps
  ├── Phase 4: Spec      → spec_writer produces formal spec
  └── Phase 5: Review    → reviewer verifies spec completeness
  │
  ├── Save spec to .qarin/spec/<slug>.md
  ├── Save task record to .qarin/tasks/<slug>.json
  └── Return TeamCompletionResult
```

**Autonomous command execution:** Every agent receives a command knowledge
block listing all available slash commands.  Agents may include
`[CMD: /command args]` directives in their output; the loop detects and
executes them, feeding results back into subsequent phase context.

---

## 11. Hook System — `server/hook_runner.py`

13 lifecycle hooks run at key moments:

| # | Hook | When | Can Modify |
|---|------|------|------------|
| 1 | `Setup` | On init/maintenance | Context injection |
| 2 | `SessionStart` | Session begins | System prompt |
| 3 | `SessionEnd` | Session ends | — |
| 4 | `UserPromptSubmit` | Before processing input | Can deny |
| 5 | `PreToolUse` | Before tool execution | Can deny/allow |
| 6 | `PostToolUse` | After tool completion | — |
| 7 | `PostToolUseFailure` | Tool execution failed | — |
| 8 | `PermissionRequest` | Permission dialog | Auto-allow read-only |
| 9 | `SkillTrigger` | Skill invokes hook | Context injection |
| 10 | `PreCompact` | Before compaction | — |
| 11 | `Stop` | Model finishes | — |
| 12 | `SubagentStart` | Subagent spawns | — |
| 13 | `SubagentStop` | Subagent finishes | — |
| 14 | `Notification` | Notable events | — |

**Pipeline:** `skill → hook → .py` — hooks are Python scripts in
`.qarin/hooks/` that receive JSON payload via stdin and return
structured results (permissionDecision, additionalContext, updatedInput).

---

## 12. Agent Communication — `runner/agent_comm.py`

Thread-safe message bus for agent-to-agent coordination:

```
AgentCommBus
  ├── send(sender, recipient, content, type)
  │     └── type: "task" | "result" | "broadcast"
  ├── receive(recipient)  → list[AgentMessage]
  ├── broadcast(sender, content)
  └── get_token_savings() → estimated savings vs context injection
```

Direct messaging costs ~1/3 of context injection tokens.

---

## 13. Memory Layer — `runner/memory_layer.py`

Persistent knowledge store across sessions:

```
MemoryLayer
  ├── store(key, content, category, importance)
  │     └── categories: fact, preference, context, learned
  ├── recall_relevant(query) → matching entries
  ├── get_context_block(max_tokens) → compact memory string
  ├── get_all_entries() → all stored entries
  └── persist() / load() → .qarin/memory.json
```

Entries are ranked by `importance × access_frequency` for retrieval.

---

## 14. Token Counter — `runner/token_counter.py`

Provider-aware usage tracking with cost estimation:

```
TokenCounter.update(provider_response)
  ├── Extract tokens via provider-specific parser:
  │     ├── Ollama:    eval_count, prompt_eval_count
  │     ├── Claude:    usage.input_tokens, output_tokens
  │     ├── Gemini:    usageMetadata.promptTokenCount
  │     └── OpenAI/HF: usage.prompt_tokens, completion_tokens
  │
  ├── Update running totals
  ├── Calculate cost from _COST_PER_MILLION table
  └── Compute tokens_per_second
```

---

## 15. Skills & Tools — `skills/tools.py`

Built-in tool capabilities exposed to the model:

| Tool | Description |
|------|-------------|
| `file_read` | Read file contents |
| `file_write` | Write/create files |
| `file_edit` | Edit file sections |
| `shell_exec` | Execute shell commands |
| `grep_search` | Search file contents |
| `web_fetch` | Fetch web pages |

**Permission model:** `PreToolUse` hook validates before execution;
`.qarinignore` patterns exclude sensitive paths.

---

## 16. Configuration — `.qarin/`

```
.qarin/
├── settings.json     ← Hook config + agent_models + intent classifier
├── chain.json        ← Wave definitions + merge policy + UI layout
├── mcp.json          ← MCP server configuration
├── memory.json       ← Persistent memory entries
├── spec/             ← Generated specs from /complete_w_team
├── tasks/            ← Task records (plan/build status)
├── hooks/            ← 13 lifecycle hook scripts
│   ├── setup.py
│   ├── session_start.py / session_end.py
│   ├── user_prompt_submit.py
│   ├── pre_tool_use.py / post_tool_use.py
│   ├── skill_trigger.py / permission_request.py
│   ├── pre_compact.py / stop.py
│   ├── subagent_start.py / subagent_stop.py
│   └── notification.py
└── status_lines/     ← Status bar display modules
```

---

## 17. Request Lifecycle — Complete Path

```
User types: "Build a REST API for user management"

1. InputArea captures text
2. CommandProcessor.dispatch() → not a slash command
3. IntentClassifier.classify()
   → agent_type="code", confidence=0.85
4. Session.send(message, agent_type="code")
5. Fire UserPromptSubmit hook → allowed
6. ContextManager.add_message("user", message)
7. Inject MemoryLayer context block
8. ProviderRouter.route("coding", messages, agent_type="code")
   ├── Resolve: provider=ollama, model=codestral:latest
   ├── OllamaProvider.chat(messages, model="codestral:latest")
   └── Response: {content: "...", eval_count: 450, ...}
9. TokenCounter.update(response)
   → prompt=1200, completion=450, cost=$0.0002
10. ContextManager.add_message("assistant", response.content)
11. Check auto-compact: 1650/4096 = 40% → no compact needed
12. Fire Stop hook
13. Display response in ChatMessageArea
14. Update StatusBar (tokens, context%, cost)
```

---

## 18. Multi-Agent Request Lifecycle

```
User types: "/complete_w_team Build a REST API"

1. CommandProcessor.dispatch("/complete_w_team Build a REST API")
2. _cmd_complete_w_team() → TeamCompletionLoop(session, command_processor)
3. TeamCompletionLoop.run("Build a REST API")
   │
   ├── Phase 1: analyst → Session.send(prompt, agent_type="analysis")
   │   ├── Agent receives command knowledge block
   │   ├── Agent output may contain [CMD: /status] → auto-executed
   │   └── Results fed to next phase
   │
   ├── Phase 2: planner → Session.send(prompt, agent_type="plan")
   │   └── Creates step-by-step implementation plan
   │
   ├── Phase 3: validator → Session.send(prompt, agent_type="review")
   │   └── Risk register, readiness score
   │
   ├── Phase 4: spec_writer → Session.send(prompt, agent_type="code")
   │   └── Formal spec with Objective/Scope/Requirements/Steps
   │
   └── Phase 5: reviewer → Session.send(prompt, agent_type="review")
       └── Completeness check, final verdict
   │
4. Save spec to .qarin/spec/build-a-rest-api.md
5. Save task record to .qarin/tasks/build-a-rest-api.json
6. Store in MemoryLayer
7. Display summary + "To execute: /build .qarin/spec/build-a-rest-api.md"
```

---

*This document describes the system as implemented.  For planned features
see [ROADMAP.md](ROADMAP.md) and [TODO.md](TODO.md).*
