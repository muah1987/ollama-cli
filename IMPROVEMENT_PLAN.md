# Ollama CLI — Improvement Plan

> Generated: 2024-02-13 | Based on project analysis and existing TODO/ROADMAP

---

## Executive Summary

Ollama CLI is a mature v0.1.0 production-ready project with:
- ✅ Multi-provider support (Ollama, Claude, Gemini, Codex, HF)
- ✅ 13 lifecycle hooks with skill→hook→.py pipeline
- ✅ MCP integration, chain orchestration, session persistence
- ✅ 7,000+ lines of tests across 27 test files
- ✅ Comprehensive documentation

This plan outlines improvements across **6 priority tiers**.

---

## 🔴 Tier 1: Critical (v0.2.0 - Production Hardening)

### 1.1 Test Coverage Enhancement
**Current State**: 7,017 lines of tests, but no coverage metrics

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Add pytest-cov for coverage reporting | High | 1h | High |
| Target 80% coverage minimum | High | 4h | High |
| Add mutation testing (mutmut) | Medium | 2h | Medium |
| Create coverage badge for README | Low | 30min | Low |

**Action Items**:
```bash
# Add to pyproject.toml
[project.optional-dependencies]
dev = [..., "pytest-cov>=4.0.0", "mutmut>=2.0.0"]

# Run coverage
pytest --cov=ollama_cmd --cov=api --cov=runner --cov=model --cov=server --cov-report=xml
```

### 1.2 CI/CD Pipeline Hardening
**Current State**: Workflows exist but may need updates

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Add coverage report to PR checks | High | 1h | High |
| Add security scanning (safety, bandit) | High | 2h | High |
| Add type checking (mypy) to CI | High | 1h | Medium |
| Matrix testing (Python 3.11, 3.12, 3.13) | Medium | 2h | Medium |
| Add benchmark regression tests | Low | 4h | Medium |

### 1.3 Error Handling & Resilience
**Current State**: Basic error handling exists

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Unified error hierarchy (`api/errors.py`) | High | 3h | High |
| Graceful degradation on provider failure | High | 4h | High |
| User-friendly error messages | Medium | 2h | High |
| Retry logic with exponential backoff | Medium | 3h | Medium |
| Circuit breaker pattern for providers | Low | 4h | Medium |

---

## 🟠 Tier 2: High Priority (v0.3.0 - Feature Completion)

### 2.1 RDMA Acceleration (From ROADMAP)
**Status**: Partially implemented

| Component | Status | Priority | Effort |
|-----------|--------|----------|--------|
| `api/rdma_client.py` | Exists, needs completion | High | 8h |
| `runner/rdma_manager.py` | Exists, needs completion | High | 8h |
| USB<>RDMA driver | Not started | Medium | 16h |
| Thunderbolt<>RDMA driver | Not started | Medium | 16h |
| Network<>RDMA driver | Not started | Medium | 16h |

### 2.2 Automatic Ollama Installation
**Status**: Script exists, needs platform support

| Platform | Status | Priority | Effort |
|----------|--------|----------|--------|
| Linux (systemctl) | Partial | High | 4h |
| macOS (homebrew) | Partial | High | 4h |
| Windows (WSL2) | Not started | High | 8h |
| Post-install health check | Not started | High | 2h |
| Service auto-start | Not started | Medium | 3h |

### 2.3 Provider Enhancements

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Add OpenAI GPT-4o support | High | 4h | High |
| Add local file model support | Medium | 8h | Medium |
| Provider health monitoring dashboard | Medium | 6h | High |
| Auto-fallback chain configuration | Medium | 4h | High |
| Cost optimization routing | Low | 6h | Medium |

---

## 🟡 Tier 3: Medium Priority (v0.4.0 - Quality & UX)

### 3.1 Code Quality

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Add mypy strict mode | High | 8h | High |
| Refactor `interactive.py` (106KB!) | High | 16h | High |
| Add docstrings to all public APIs | Medium | 8h | Medium |
| Create architecture diagrams | Medium | 4h | Medium |
| Code complexity metrics (radon) | Low | 2h | Low |

### 3.2 User Experience

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| First-run onboarding wizard | High | 8h | High |
| Interactive model selection menu | Medium | 4h | High |
| Better progress indicators | Medium | 4h | Medium |
| Command autocomplete (argcomplete) | Medium | 3h | High |
| Color theme customization | Low | 4h | Low |

### 3.3 Documentation

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| API reference docs (Sphinx) | High | 16h | High |
| Video tutorials | Medium | 8h | Medium |
| Contribution guide expansion | Medium | 4h | Medium |
| FAQ section | Low | 2h | Medium |
| Changelog automation | Low | 2h | Low |

---

## 🟢 Tier 4: Future Features (v0.5.0+)

### 4.1 BubbleTea Migration (From ROADMAP)
**Status**: Planned migration to Go/BubbleTea

| Phase | Description | Effort |
|-------|-------------|--------|
| Research | Evaluate BubbleTea capabilities | 8h |
| Prototype | Create proof-of-concept | 40h |
| Migration | Port frontend to Go | 80h+ |
| Compatibility | Python API bridge | 16h |

### 4.2 Advanced Features

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Voice input/output | Low | 24h | Medium |
| Web UI companion | Low | 40h | Medium |
| Plugin system | Medium | 24h | High |
| Agent marketplace | Low | 80h | Medium |
| Multi-agent orchestration | Medium | 40h | High |

### 4.3 Performance Optimizations

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Async/await throughout | Medium | 16h | High |
| Response streaming | Medium | 8h | High |
| Memory optimization | Low | 8h | Medium |
| Startup time reduction | Low | 4h | Low |

---

## 🔵 Tier 5: Infrastructure & Tooling

### 5.1 Development Experience

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Pre-commit hooks (ruff, mypy, bandit) | High | 2h | High |
| VS Code devcontainer | Medium | 4h | Medium |
| Docker development image | Medium | 4h | Medium |
| Makefile for common tasks | Low | 2h | Low |
| Development seed script | Low | 2h | Low |

### 5.2 Monitoring & Observability

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Structured logging (structlog) | Medium | 4h | High |
| OpenTelemetry integration | Low | 8h | Medium |
| Usage analytics (opt-in) | Low | 8h | Low |
| Performance profiling hooks | Low | 4h | Low |

---

## ⚪ Tier 6: Nice to Have

### 6.1 Extended Integrations

- Git hooks integration (pre-commit AI review)
- IDE extensions (VS Code, Neovim)
- Shell integrations (zsh, fish, bash)
- CI/CD pipeline generators

### 6.2 Community Building

- Discord/Slack community
- Contributor recognition system
- Hackathon events
- Blog post series

---

## Implementation Roadmap

### Sprint 1 (Weeks 1-2): Critical Fixes
- [ ] Add pytest-cov and coverage targets
- [ ] Add security scanning to CI
- [ ] Create unified error hierarchy
- [ ] Add mypy to CI pipeline

### Sprint 2 (Weeks 3-4): High Priority
- [ ] Complete RDMA client implementation
- [ ] Add Windows WSL2 installation support
- [ ] Implement provider fallback chain

### Sprint 3 (Weeks 5-6): Quality Improvements
- [ ] Refactor interactive.py into modules
- [ ] Add first-run onboarding wizard
- [ ] Set up Sphinx documentation

### Sprint 4 (Weeks 7-8): Future Prep
- [ ] Research BubbleTea migration
- [ ] Design plugin system architecture
- [ ] Performance benchmarking suite

---

## Metrics & Success Criteria

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Test Coverage | Unknown | 80% | Sprint 1 |
| Python Support | 3.11-3.13 | 3.11-3.13 | ✅ |
| Provider Count | 5 | 6+ | Sprint 2 |
| Documentation | Good | Excellent | Sprint 3 |
| Install Success Rate | Unknown | 95%+ | Sprint 2 |

---

## Quick Wins (Can Do Today)

1. **Add coverage badge to README** (5 min)
   ```markdown
   ![Coverage](https://img.shields.io/badge/coverage-unknown-yellow)
   ```

2. **Add pre-commit config** (15 min)
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.0
       hooks:
         - id: ruff
   ```

3. **Add security scan to CI** (20 min)
   ```yaml
   # Add to .github/workflows/build-test.yml
   - name: Security Scan
     run: |
       pip install safety bandit
       safety check
       bandit -r ollama_cmd api runner model server
   ```

4. **Add mypy to CI** (10 min)
   ```yaml
   - name: Type Check
     run: mypy ollama_cmd api runner model server --ignore-missing-imports
   ```

---

## Dependencies & Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| RDMA driver complexity | High | High | Start with network<>RDMA only |
| BubbleTea learning curve | Medium | High | Prototype first |
| Provider API changes | Medium | Medium | Abstract provider layer |
| Test flakiness | Low | Medium | Mock external services |

---

*This plan is a living document. Update as priorities shift and tasks are completed.*