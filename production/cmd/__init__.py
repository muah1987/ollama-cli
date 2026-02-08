"""Command package -- CLI entry points matching Ollama's command structure.

This package contains individual command modules that mirror Ollama's CLI:
- root: Main entry point and argument parsing
- run: Generate responses from a prompt
- list: List available local models
- pull: Pull a model from the registry
- show: Show model details
- serve: Check/manage Ollama server status
- config: Show/set provider configuration
- status: Show current session status
- version: Show CLI version
- interactive: Start interactive REPL mode
"""