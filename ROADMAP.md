# Ollama CLI Roadmap

A comprehensive roadmap for the Ollama CLI project, tracking current priorities and future development.

---

## Current Status: v0.2.0 (Production)

> **⚠️ Migration Notice:** The CLI frontend is migrating from Python/readline
> to [BubbleTea](https://github.com/charmbracelet/bubbletea) (Go).  The API
> layer and provider integrations remain unchanged.  See
> [Phase 6](#phase-6-bubbletea-migration) below for details.

### Recently Completed
- [x] Multi-provider routing (Ollama, Claude, Gemini, Codex, Hugging Face)
- [x] Auto-compact context management
- [x] 13 lifecycle hooks (Setup, SessionStart/End, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, SkillTrigger, PreCompact, Stop, SubagentStart/Stop, Notification)
- [x] Skill→Hook→.py pipeline
- [x] MCP integration (GitHub, Docker, filesystem, memory servers)
- [x] Chain orchestration (multi-wave subagent pipeline)
- [x] Multi-model agent assignment (5+ models with mixed providers)
- [x] Status line dashboards (token counter, provider health, full dashboard)
- [x] Interactive REPL mode with persistent bottom status bar (cwd, UUID, model, context%, job status)
- [x] Token tracking and cost estimation
- [x] Session persistence
- [x] GH_TOKEN and HF_TOKEN support
- [x] Dependabot with auto-merge for patch/minor updates
- [x] Textual TUI as primary interface (removed legacy readline)
- [x] Unified error hierarchy (`api/errors.py`)
- [x] CI/CD with coverage reporting, linting, security scanning
- [x] Coverage and CI badges in README

### Current Priority: Feature Completion (v0.3.0)

---

## Phase 1: Core Enhancements (v0.3.0 - v0.4.0)

### Feature: Automatic Ollama Installation
**Timeline**: Q1 2024
**Priority**: High

- [ ] `install.sh` script that detects and installs Ollama
- [ ] Support for Linux (systemctl service management)
- [ ] Support for macOS (homebrew or direct download)
- [ ] Support for Windows (WSL2 native support)
- [ ] Post-installation health check
- [ ] Automatic service start configuration

### Feature: Claude-Code Integration
**Timeline**: Q1 2024
**Priority**: High

- [ ] Document CLI as reference implementation for Claude-Code
- [ ] Ensure hook compatibility with Claude-Code hook events
- [ ] Create testing examples matching Claude-Code patterns
- [ ] Integration documentation

---

## Phase 2: High-Performance Computing (v0.5.0 - v0.6.0)

### Feature: RDMA Acceleration Support
**Timeline**: Q2 2024
**Priority**: Medium

- [ ] RMDA communication protocol implementation (`api/rdma_client.py`)
- [ ] Device detection and configuration (`runner/rdma_manager.py`)
- [ ] USB<>RDMA driver
- [ ] Thunderbolt<>RDMA driver
- [ ] Network<>RDMA driver
- [ ] Automatic clustering support

### Feature: MLX Integration
**Timeline**: Q2 2024
**Priority**: Medium

- [ ] MLX device detection
- [ ] Metal performance shaders acceleration
- [ ] Automatic device selection
- [ ] Optimized inference for Apple Silicon

### Feature: EXO Integration
**Timeline**: Q2 2024
**Priority**: Medium

- [ ] EXO execution acceleration
- [ ] Distributed execution support
- [ ] Load balancing across nodes
- [ ] Configuration management

---

## Phase 3: Advanced Features (v0.7.0 - v0.8.0)

### Feature: Model Management
**Timeline**: Q3 2024
**Priority**: Medium

- [ ] Full `pull` command implementation
- [ ] Full `show` command implementation
- [ ] Full `create` command implementation
- [ ] Full `rm` command implementation
- [ ] Full `cp` command implementation
- [ ] Full `ps` command implementation
- [ ] Full `stop` command implementation
- [ ] Full `config` command implementation
- [ ] Full `status` command implementation

### Feature: Advanced Context Management
**Timeline**: Q3 2024
**Priority**: Medium

- [ ] Semantic compression for long contexts
- [ ] Key information extraction before compaction
- [ ] Customizable compaction strategies
- [ ] Context export/import

---

## Phase 4: Production Enhancements (v0.9.0 - v1.0.0)

### Feature: Production Readiness
**Timeline**: Q4 2024
**Priority**: High

- [ ] Comprehensive test suite
- [ ] Integration with CI/CD workflows
- [ ] Performance profiling and optimization
- [ ] Memory usage optimization
- [ ] Error handling and logging improvements

### Feature: Security & Privacy
**Timeline**: Q4 2024
**Priority**: High

- [ ] Secure RDMA communication with encryption
- [ ] API key validation
- [ ] Input sanitization
- [ ] Hook command validation
- [ ] Audit logging

---

## Phase 5: Future Enhancements (v1.1.0+)

### Feature: GPU Acceleration
**Timeline**: TBA
**Priority**: Low

- [ ] GPU detection and configuration
- [ ] CUDA support for NVIDIA GPUs
- [ ] ROCm support for AMD GPUs
- [ ] Automatic GPU memory management

### Feature: Distributed Computing
**Timeline**: TBA
**Priority**: Low

- [ ] Cluster configuration
- [ ] Distributed inference
- [ ] Load balancing across nodes
- [ ] Fault tolerance

### Feature: Network Optimization
**Timeline**: TBA
**Priority**: Low

- [ ] Network topology optimization
- [ ] Auto-scaling based on workload
- [ ] Bandwidth throttling
- [ ] Connection pooling

### Feature: Developer Tools
**Timeline**: TBA
**Priority**: Low

- [ ] CLI plugins system
- [ ] Custom provider support
- [ ] Extensibility framework
- [ ] Plugin marketplace

---

## Phase 6: BubbleTea Migration

### Feature: Go/BubbleTea TUI Rewrite
**Timeline**: TBA
**Priority**: High

The CLI frontend will be rewritten in Go using the
[BubbleTea](https://github.com/charmbracelet/bubbletea) TUI framework from
Charm.  This brings a richer terminal UI, better cross-platform support, and
a single static binary.

**Reference projects:**

- [ollama/ollama](https://github.com/ollama/ollama) — Ollama server (Go)
- [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) — Gemini CLI
- [openai/codex](https://github.com/openai/codex) — OpenAI Codex CLI
- [charmbracelet/bubbletea](https://github.com/charmbracelet/bubbletea) — TUI framework
- [opencode-ai/opencode](https://github.com/opencode-ai/opencode) — OpenCode CLI

**Migration plan:**

- [ ] Initialise Go module and BubbleTea project scaffold
- [ ] Port provider routing (Ollama, Claude, Gemini, Codex, HF) to Go
- [ ] Implement BubbleTea TUI with streaming chat view
- [ ] Port slash commands (`/model`, `/provider`, `/status`, `/compact`, `/init`, etc.)
- [ ] Port lifecycle hook system (13 hooks)
- [ ] Port MCP integration
- [ ] Port chain orchestration
- [ ] Port context management and auto-compact
- [ ] Single-binary distribution (no Python/uv dependency)
- [ ] Archive current Python implementation to `ollama-cli.bak/`

---

## Implementation Notes

### Versioning Strategy
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Process
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Publish to PyPI

---

*Last updated: 2026-02-14*
*This document is maintained by the project team.*
