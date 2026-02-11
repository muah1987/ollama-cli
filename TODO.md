# Ollama CLI TODO List

Current task priorities and pending work for the Ollama CLI project.

---

## Production Readiness (Critical)

### In Progress
- [ ] Complete production folder structure
- [ ] Update pyproject.toml with all dependencies
- [ ] Fix GitHub workflows for production folder

### High Priority
- [ ] Create automatic Ollama installation script (`install.sh`)
- [ ] Implement `.ollama/hooks/install_ollama.py` hook
- [ ] Update GitHub workflows to work with production folder
- [ ] Copy all test files to production/tests/

### Medium Priority
- [ ] Create ROADMAP.md (IN PROGRESS)
- [ ] Create TODO.md (IN PROGRESS)
- [ ] Update README.md with production folder structure
- [ ] Update docs/development.md paths
- [ ] Update docs/api.md paths

---

## Feature Development

### RDMA Acceleration (High Priority)
- [ ] Create `api/rdma_client.py` with RMDA protocol
- [ ] Create `runner/rdma_manager.py` with device detection
- [ ] Implement USB<>RDMA driver
- [ ] Implement Thunderbolt<>RDMA driver
- [ ] Implement Network<>RDMA driver
- [ ] Create MLX integration in `skills/mlx/`
- [ ] Create EXO integration in `skills/exo/`
- [ ] Create RDMA skill in `skills/rdma/`
- [ ] Update skills/manifest.md
- [ ] Update skills/__init__.py with new skills

### Command Implementation (Medium Priority)
- [ ] Implement `pull` command
- [ ] Implement `show` command
- [ ] Implement `create` command
- [ ] Implement `rm` command
- [ ] Implement `cp` command
- [ ] Implement `ps` command
- [ ] Implement `stop` command
- [ ] Implement `config` command
- [ ] Implement `status` command

### Test Enhancement
- [ ] Create `tests/test_rdma.py`
- [ ] Create `tests/test_install.py`
- [ ] Create `tests/test_claude_code_integration.py`
- [ ] Fix `conftest.py` for production structure
- [ ] Add integration tests

---

## Documentation

### High Priority
- [ ] Update README.md paths
- [ ] Create comprehensive developer onboarding guide
- [ ] Document RDMA acceleration
- [ ] Document automatic installation process

### Medium Priority
- [ ] Add API documentation
- [ ] Add CLI command reference
- [ ] Document hook system
- [ ] Document skill framework

---

## Infrastructure

### GitHub Actions
- [ ] Update `build-test.yml`
- [ ] Fix test path references
- [ ] Update cache paths
- [ ] Add production folder validation step
- [ ] Update release workflows
- [ ] Update pypi-publish.yml

### CI/CD
- [ ] Add automated testing on PR
- [ ] Add code coverage reporting
- [ ] Add security scanning
- [ ] Add dependency updates

---

## Known Issues

### Critical
- None currently

### Medium
- CLI may need additional command implementations
- Some tests may need path updates

### Low
- Documentation may need minor updates

---

*Last updated: 2026-02-11*
*This document is maintained by the project team.*
