# ollama-cli Unit Tests

This directory contains comprehensive unit tests for the ollama-cli application.

## Test Coverage

The tests cover:

1. **Token counting logic** for all providers (Ollama, Anthropic, Google, OpenAI, HF)
2. **Context compression** with nested sub-agent scenarios
3. **CLI integration** tests for token display and cost estimation
4. **Multi-model agent configuration** for mixed provider setups
5. **MCP client** configuration, server management, and tool discovery
6. **Chain controller** multi-wave orchestration pipeline
7. **Hook system** including all 13 lifecycle hooks and skill→hook→.py pipeline
8. **Status bar** job tracking (idle/thinking/compacting/planning/building)
9. **Edge cases** like zero tokens, maximum context limits
10. **Invalid provider handling**

## Test Files

- `test_token_counter.py` - Core token counting functionality
- `test_subagent_scenarios.py` - Nested sub-agent and context compression tests
- `test_cli_integration.py` - CLI integration tests
- `test_multi_model_hooks.py` - Multi-model config, status bar, skill trigger pipeline
- `test_mcp_client.py` - MCP client and server management
- `test_chain_controller.py` - Chain controller and wave orchestration
- `conftest.py` - Pytest configuration and fixtures

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/test_multi_model_hooks.py -v
uv run pytest tests/test_mcp_client.py -v
uv run pytest tests/test_chain_controller.py -v
```

## Requirements

- Python 3.11+
- pytest (installed via `uv sync --dev`)
