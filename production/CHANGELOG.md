## [1.2.0] - 2026-02-11

### Added
- Hugging Face provider integration with OpenAI-compatible API routing
- Agent model assignment feature allowing specific models per agent type (@code, @research, etc.)
- New interactive mode commands: /set-agent-model and /list-agent-models
- Environment variable support for agent model configuration
- JSON configuration file support for agent model assignments
- Comprehensive documentation for Hugging Face and agent model assignment
- Guide for adding new providers (docs/adding_providers.md)

### Changed
- Enhanced ProviderRouter to support agent-specific model routing
- Extended Session class to work with ProviderRouter for actual API calls
- Updated README.md with new features and documentation
- Enhanced CLI reference documentation with agent commands
- Improved multi-provider documentation with Hugging Face integration
