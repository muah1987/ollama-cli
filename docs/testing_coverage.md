# Testing and Code Coverage

Ollama CLI maintains high quality standards through comprehensive testing and code coverage measurement.

## Running Tests

To run the test suite locally:

```bash
# Run all tests
uv run pytest tests/ -v

# Run tests with coverage reporting
uv run pytest tests/ --cov=./ --cov-report=html --cov-report=term-missing

# Run tests with coverage and minimum threshold
uv run pytest tests/ --cov=./ --cov-report=term-missing --cov-fail-under=80
```

## Code Coverage Policy

All contributions to Ollama CLI must maintain a minimum of 80% code coverage. The CI/CD pipeline enforces this requirement automatically.

Coverage reports are generated in multiple formats:
- Terminal output with missing line indicators
- HTML reports for detailed analysis
- XML reports for integration with coverage services

## Test Structure

Tests are organized to mirror the source code structure:

```
tests/
├── test_integration.py           # Integration tests
├── test_cli_parsing.py           # CLI argument parsing
├── test_unit_tests.py            # Unit tests
├── test_hook_system.py          # Hook system functionality
├── test_mcp_integration.py      # MCP server integration
├── test_provider_routing.py     # Multi-provider routing
└── ...                         # Additional test modules
```

## Writing Tests

When adding new features, ensure comprehensive test coverage:

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test interactions between components
3. **CLI Tests**: Test command-line interface behavior
4. **Edge Cases**: Test error conditions and boundary values

Example test structure:

```python
def test_example_function():
    """Test the example_function with valid inputs."""
    # Arrange
    input_data = "test input"

    # Act
    result = example_function(input_data)

    # Assert
    assert result == "expected output"
```

## Continuous Integration

GitHub Actions automatically runs the test suite with coverage measurement on all pushes and pull requests. Tests must pass and maintain the minimum coverage threshold for merging.

## Coverage Reports

Coverage reports are uploaded to Codecov.io for visualization and tracking. Team members can view detailed coverage information and identify areas requiring additional test coverage.

## Troubleshooting

Common testing issues and solutions:

1. **Missing test dependencies**: Ensure all development dependencies are installed with `uv sync --dev`
2. **Test isolation issues**: Use pytest fixtures to properly isolate tests
3. **Async test timing**: Use `pytest-asyncio` with appropriate markers for async tests
4. **Environment variables**: Set required environment variables for tests that need them

For further assistance with testing, see the [Development Guide](development.md).