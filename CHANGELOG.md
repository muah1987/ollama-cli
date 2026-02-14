## [0.2.0] - 2026-02-14

### Added
- Unified error hierarchy in `api/errors.py` with centralized exception classes
- `OllamaCliError` root exception with `user_message` property and `hint` support
- New error types: `ProviderRateLimitError`, `ProviderResponseError`, `ConfigurationError`, `SessionError`
- CI security scanning via bandit
- Coverage, CI, Python version, and license badges in README
- Test suite for error hierarchy (23 new tests)
- Textual TUI as the primary and only interface (removed legacy readline REPL)
- Code coverage reporting in CI workflows with 75% minimum requirement
- `/complete_w_team` agentic sub-agent completion loop (analyse→plan→validate→spec→review)
- Autonomous command execution: agents can invoke slash commands via `[CMD: /command]` directives
- Command knowledge injection into all team completion agents
- `team` and `research` agent types in intent classifier
- Comprehensive system workflow documentation (`docs/SYSTEM_WORKFLOW.md`)
- 34 new tests for team completion loop

### Changed
- Simplified CLI interface to focus exclusively on Textual TUI
- Updated development workflow to emphasize TUI-first approach
- Enhanced CI/CD pipeline with test coverage enforcement

### Removed
- Legacy readline-based REPL interface
- Classic CLI mode (--classic flag removed)

## [0.1.0] - 2026-02-12

### Added
- Hugging Face provider integration with OpenAI-compatible API routing
- Agent model assignment feature allowing specific models per agent type (@code, @research, etc.)
- New interactive mode commands: /set-agent-model and /list-agent-models
- Environment variable support for agent model configuration
- JSON configuration file support for agent model assignments
- Comprehensive documentation for Hugging Face and agent model assignment
- Guide for adding new providers (docs/adding_providers.md)
- Auto-discovery of local Ollama models at startup with intelligent model resolution
- Persistent bottom status bar using ANSI escape sequences (three-zone terminal layout)

### Changed
- Enhanced ProviderRouter to support agent-specific model routing
- Extended Session class to work with ProviderRouter for actual API calls
- Updated README.md with new features and documentation
- Enhanced CLI reference documentation with agent commands
- Improved multi-provider documentation with Hugging Face integration

### Fixed
- Provider fallback routing now uses the user's selected model instead of hardcoded `llama3.2` default
- Status bar pinned to terminal bottom so prompt `>>>` stays in the MID zone
- Session.send() passes session model to ProviderRouter for correct model resolution
