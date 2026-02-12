# Ollama CLI TODO List

Current task priorities and pending work for the Ollama CLI project.

---

## Production Readiness (Critical)

### Completed
- [x] Multi-provider routing (Ollama, Claude, Gemini, Codex, HF)
- [x] 13 lifecycle hooks with skill→hook→.py pipeline (15 hook scripts)
- [x] Multi-model agent assignment (5+ models, mixed providers, 10 agent types)
- [x] MCP integration (GitHub, Docker, filesystem, memory servers)
- [x] Chain orchestration (multi-wave subagent pipeline: analyze→plan→execute→finalize)
- [x] Terminal layout fix (persistent bottom status bar with job status)
- [x] GH_TOKEN and HF_TOKEN support in config and `.env.sample`
- [x] Dependabot with auto-merge for patch/minor updates
- [x] Updated all documentation files (15 docs, 6 root `.md` files)
- [x] Update pyproject.toml with all dependencies, `skills` in wheel, classifiers, URLs
- [x] Agent communication bus (`runner/agent_comm.py`)
- [x] Memory layer (`runner/memory_layer.py`)
- [x] Interactive REPL with 25+ slash commands (`cmd/interactive.py`)
- [x] Session persistence with save/load/resume
- [x] Auto-compact context management at 85% threshold
- [x] Token tracking and cost estimation across all providers

### Infrastructure — Completed
- [x] `install.sh` — automatic Ollama installation script
- [x] `.ollama/hooks/install_ollama.py` — installation hook
- [x] `.github/workflows/build-test.yml` — runs tests, lint, type check, structure validation
- [x] `.github/workflows/autorelease.yml` — automated releases
- [x] `.github/workflows/release.yml` — manual release workflow
- [x] `.github/workflows/pypi-publish.yml` — PyPI publishing
- [x] `.github/workflows/auto-merge-dependabot.yml` — auto-merge Dependabot PRs
- [x] `.github/dependabot.yml` — dependency update config
- [x] `conftest.py` — pytest configuration with importlib mode

### Commands — Implemented
- [x] `interactive` / `chat` / `i` — interactive REPL (fully implemented)
- [x] `run` — one-shot prompt (fully implemented)
- [x] `list` — list local models (fully implemented)
- [x] `serve` — check Ollama server status (fully implemented)
- [x] `version` — show CLI version (fully implemented)
- [x] `show` — show model details (implemented)
- [x] `create` — create a model (implemented)
- [x] `rm` — remove a model (implemented)
- [x] `cp` — copy a model (implemented)
- [x] `ps` — list running models (implemented)
- [x] `stop` — stop a running model (implemented)

### Commands — Stub (coming soon)
- [ ] `pull` — pull a model from registry (stub, prints "coming soon")
- [ ] `config` — show/set configuration from CLI (stub; works in REPL via `/config`)
- [ ] `status` — show session status from CLI (stub; works in REPL via `/status`)

### RDMA Acceleration — Implemented (framework)
- [x] `api/rdma_client.py` — RDMA communication protocol
- [x] `runner/rdma_manager.py` — device detection and management
- [x] `skills/rdma/` — RDMA skill module
- [x] `skills/mlx/` — Apple Metal MLX acceleration skill
- [x] `skills/exo/` — EXO distributed execution skill
- [x] `skills/manifest.md` — skills documentation with skill→hook→.py pipeline
- [ ] USB<>RDMA driver — transport layer (framework only)
- [ ] Thunderbolt<>RDMA driver — transport layer (framework only)
- [ ] Network<>RDMA driver — transport layer (framework only)

### Tests — 286 passing, 4 skipped (17 test files)
- [x] `test_token_counter.py` — token counting for all providers
- [x] `test_subagent_scenarios.py` — nested sub-agents and context compression
- [x] `test_cli_integration.py` — CLI integration tests
- [x] `test_cli_parser.py` — CLI argument parsing
- [x] `test_basic.py` — basic sanity tests
- [x] `test_ollama_cli_comprehensive.py` — comprehensive module tests
- [x] `test_context_manager_subagents.py` — context manager sub-agent tests
- [x] `test_auto_compact.py` — auto-compaction tests
- [x] `test_build_and_integration.py` — build and integration tests
- [x] `test_agent_comm_memory.py` — agent comm bus and memory layer
- [x] `test_gemini_codex_features.py` — Gemini and Codex provider features
- [x] `test_claude_code_integration.py` — Claude Code integration tests
- [x] `test_rdma.py` — RDMA module tests
- [x] `test_install.py` — installation tests
- [x] `test_multi_model_hooks.py` — multi-model config, status bar, hook pipeline
- [x] `test_mcp_client.py` — MCP client and server management
- [x] `test_chain_controller.py` — chain controller and wave orchestration

### Documentation — Complete (15 docs + 6 root files)
- [x] `README.md` — project overview with all features
- [x] `CONTRIBUTING.md` — contribution guide with updated project structure
- [x] `SECURITY.md` — security policy
- [x] `ROADMAP.md` — project roadmap with completed milestones
- [x] `CHANGELOG.md` — changelog
- [x] `OLLAMA.md` — project context for AI assistants
- [x] `.github/README.md` — documentation index with all features
- [x] `.github/copilot-instructions.md` — Copilot instructions with hooks, MCP, chain
- [x] `docs/hooks.md` — all 13 lifecycle hooks documented
- [x] `docs/configuration.md` — env vars, settings, MCP config, agent models
- [x] `docs/cli_reference.md` — all commands including MCP and chain
- [x] `docs/project_overview.md` — features, architecture
- [x] `docs/multi_provider.md` — all 5 providers
- [x] `docs/agent_model_assignment.md` — multi-model agent assignment
- [x] `docs/mcp.md` — MCP server integration
- [x] `docs/rdma.md` — RDMA acceleration
- [x] `docs/getting_started.md` — installation walkthrough
- [x] `docs/development.md` — development guide
- [x] `docs/api.md` — API documentation
- [x] `docs/api_reference.md` — API reference
- [x] `docs/huggingface.md` — Hugging Face provider
- [x] `docs/adding_providers.md` — adding new providers
- [x] `skills/manifest.md` — skills manifest with skill→hook→.py pipeline
- [x] `tests/README.md` — test documentation

---

## Remaining Work

### Short Term
- [ ] Implement `pull` command (download models from registry)
- [ ] Implement `config` CLI command (currently REPL-only via `/config`)
- [ ] Implement `status` CLI command (currently REPL-only via `/status`)
- [ ] Add code coverage reporting to CI

### Medium Term
- [ ] RDMA transport drivers (USB, Thunderbolt, Network) — real hardware integration
- [ ] Streaming responses via SSE for cloud providers
- [ ] Plugin system for third-party extensions
- [ ] Web UI dashboard

### Long Term
- [ ] PyPI publishing (automated via workflow, not yet enabled)
- [ ] Multi-user session sharing
- [ ] Fine-tuning integration via Ollama
- [ ] Voice input/output via system TTS/STT

---

## Known Issues

### None Critical

### Low
- `pull`, `config`, `status` CLI commands are stubs (work fine in REPL)
- RDMA transport drivers are framework-only (no real hardware integration yet)

---

*Last updated: 2026-02-12*
*286 tests passing | 15 hook scripts | 25+ REPL commands | 5 providers | 4 MCP servers*
