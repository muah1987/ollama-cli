"""Tests for the first-time onboarding wizard."""

import json
from pathlib import Path
from unittest.mock import patch

from api.config import CliOllamaConfig, save_config
from ollama_cmd.onboarding import needs_onboarding, run_onboarding


class TestNeedsOnboarding:
    """Verify the needs_onboarding detection logic."""

    def test_needs_onboarding_when_not_completed(self) -> None:
        """Returns True when onboarding_complete is False."""
        cfg = CliOllamaConfig(onboarding_complete=False)
        with patch("ollama_cmd.onboarding.get_config", return_value=cfg):
            assert needs_onboarding() is True

    def test_no_onboarding_when_completed(self) -> None:
        """Returns False when onboarding_complete is True."""
        cfg = CliOllamaConfig(onboarding_complete=True)
        with patch("ollama_cmd.onboarding.get_config", return_value=cfg):
            assert needs_onboarding() is False

    def test_needs_onboarding_reads_from_config_json(self, tmp_path: Path) -> None:
        """Onboarding flag persists via config.json round-trip."""
        cfg = CliOllamaConfig(onboarding_complete=True)
        config_path = tmp_path / "config.json"
        save_config(cfg, config_path)

        with open(config_path) as f:
            data = json.load(f)
        assert data["onboarding_complete"] is True


class TestRunOnboarding:
    """Verify the onboarding wizard populates config correctly."""

    def test_run_onboarding_sets_provider_and_model(self, tmp_path: Path) -> None:
        """Wizard saves provider, model, and marks complete."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path) as mock_save,
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
        ):
            # Simulate user choosing gemini provider, default model, skip api key
            mock_ask.side_effect = [
                "gemini",  # provider choice
                "",  # API key (empty)
                "gemini-2.5-flash",  # model
            ]
            result = run_onboarding()

        assert result.provider == "gemini"
        assert result.ollama_model == "gemini-2.5-flash"
        assert result.onboarding_complete is True
        mock_save.assert_called_once()

    def test_run_onboarding_ollama_asks_host(self, tmp_path: Path) -> None:
        """When ollama provider is chosen, wizard asks for host URL before API key."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
        ):
            mock_ask.side_effect = [
                "ollama",  # provider
                "http://localhost:11434",  # host (asked first for ollama)
                "",  # API key (skip)
                "llama3.2",  # model
            ]
            result = run_onboarding()

        assert result.provider == "ollama"
        assert result.ollama_model == "llama3.2"
        assert result.ollama_host == "http://localhost:11434"
        assert result.onboarding_complete is True

    def test_run_onboarding_cloud_provider_sets_api_key(self, tmp_path: Path) -> None:
        """When a cloud provider is chosen, API key is stored in config."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
            patch("ollama_cmd.onboarding._fetch_provider_models", return_value=[]),
        ):
            mock_ask.side_effect = [
                "claude",  # provider
                "sk-test-key",  # API key
                "claude-sonnet-4-20250514",  # model
            ]
            result = run_onboarding()

        assert result.provider == "claude"
        assert result.anthropic_api_key == "sk-test-key"
        assert result.onboarding_complete is True

    def test_run_onboarding_numeric_provider_selection(self, tmp_path: Path) -> None:
        """Wizard accepts a 1-based number to choose a provider."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
        ):
            mock_ask.side_effect = [
                "1",  # provider by number (ollama)
                "http://localhost:11434",  # host
                "",  # API key (skip)
                "llama3.2",  # model
            ]
            result = run_onboarding()

        assert result.provider == "ollama"
        assert result.ollama_model == "llama3.2"
        assert result.ollama_host == "http://localhost:11434"
        assert result.onboarding_complete is True

    def test_run_onboarding_fetches_models_for_cloud_provider(self, tmp_path: Path) -> None:
        """When a cloud provider returns models, wizard shows them for selection."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"
        fetched = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro"]

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
            patch("ollama_cmd.onboarding._fetch_provider_models", return_value=fetched),
        ):
            mock_ask.side_effect = [
                "gemini",  # provider
                "test-gemini-key",  # API key
                "2",  # model by number (gemini-2.5-flash)
            ]
            result = run_onboarding()

        assert result.provider == "gemini"
        assert result.ollama_model == "gemini-2.5-flash"
        assert result.onboarding_complete is True

    def test_run_onboarding_model_fetch_failure_falls_back(self, tmp_path: Path) -> None:
        """When model fetching fails, wizard falls back to manual entry."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
            patch("ollama_cmd.onboarding._fetch_provider_models", return_value=[]),
        ):
            mock_ask.side_effect = [
                "claude",  # provider
                "sk-test-key",  # API key
                "claude-sonnet-4-20250514",  # model (manual)
            ]
            result = run_onboarding()

        assert result.provider == "claude"
        assert result.ollama_model == "claude-sonnet-4-20250514"
        assert result.onboarding_complete is True

    def test_run_onboarding_model_selection_by_name(self, tmp_path: Path) -> None:
        """User can type a model name from the fetched list."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"
        fetched = ["gpt-4.1", "gpt-4.1-mini", "gpt-4o"]

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
            patch("ollama_cmd.onboarding._fetch_provider_models", return_value=fetched),
        ):
            mock_ask.side_effect = [
                "codex",  # provider
                "sk-openai-key",  # API key
                "gpt-4o",  # model by name
            ]
            result = run_onboarding()

        assert result.provider == "codex"
        assert result.ollama_model == "gpt-4o"
        assert result.onboarding_complete is True

    def test_run_onboarding_ollama_with_api_key_fetches_models(self, tmp_path: Path) -> None:
        """When ollama is chosen with an API key, models are fetched from the server."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"
        fetched = ["llama3.2:latest", "codestral:latest", "qwen2:7b"]

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
            patch("ollama_cmd.onboarding._fetch_provider_models", return_value=fetched),
        ):
            mock_ask.side_effect = [
                "ollama",  # provider
                "https://ollama.example.com",  # host (cloud)
                "my-ollama-api-key",  # API key
                "2",  # model by number (codestral:latest)
            ]
            result = run_onboarding()

        assert result.provider == "ollama"
        assert result.ollama_host == "https://ollama.example.com"
        assert result.ollama_api_key == "my-ollama-api-key"
        assert result.ollama_model == "codestral:latest"
        assert result.onboarding_complete is True

    def test_run_onboarding_ollama_api_key_not_saved_to_disk(self, tmp_path: Path) -> None:
        """Ollama API key must not be persisted to config.json on disk."""
        cfg = CliOllamaConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", wraps=lambda c, p=None: save_config(c, config_path)),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
            patch("ollama_cmd.onboarding._fetch_provider_models", return_value=[]),
        ):
            mock_ask.side_effect = [
                "ollama",  # provider
                "https://ollama.example.com",  # host
                "secret-key-123",  # API key
                "llama3.2",  # model
            ]
            run_onboarding()

        with open(config_path) as f:
            data = json.load(f)
        assert "ollama_api_key" not in data
        assert "secret-key-123" not in json.dumps(data)
