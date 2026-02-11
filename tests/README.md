# ollama-cli Unit Tests

This directory contains comprehensive unit tests for the ollama-cli application.

## Test Coverage

The tests cover:

1. **Token counting logic** for all providers (Ollama, Anthropic, Google, OpenAI)
2. **Context compression** with nested sub-agent scenarios 
3. **CLI integration** tests for token display and cost estimation
4. **Edge cases** like zero tokens, maximum context limits
5. **Invalid provider handling**

## Test Files

- `test_token_counter.py` - Core token counting functionality
- `test_subagent_scenarios.py` - Nested sub-agent and context compression tests
- `test_cli_integration.py` - CLI integration tests
- `conftest.py` - Pytest configuration and fixtures

## Running Tests

### Using the test runner:
```bash
cd ollama-cli
python run_tests.py
```

### Using pytest directly:
```bash
cd ollama-cli
python -m pytest tests/ -v
```

### Running specific test files:
```bash
python -m pytest tests/test_token_counter.py -v
python -m pytest tests/test_subagent_scenarios.py -v
```

## Requirements

- pytest
- The ollama-cli src/ directory should be accessible

Install pytest with:
```bash
pip install pytest
```
