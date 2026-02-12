"""Tests for the first-time onboarding wizard."""

import json
from pathlib import Path
from unittest.mock import patch

from api.config import OllamaCliConfig, save_config
from ollama_cmd.onboarding import needs_onboarding, run_onboarding


class TestNeedsOnboarding:
    """Verify the needs_onboarding detection logic."""

    def test_needs_onboarding_when_not_completed(self) -> None:
        """Returns True when onboarding_complete is False."""
        cfg = OllamaCliConfig(onboarding_complete=False)
        with patch("ollama_cmd.onboarding.get_config", return_value=cfg):
            assert needs_onboarding() is True

    def test_no_onboarding_when_completed(self) -> None:
        """Returns False when onboarding_complete is True."""
        cfg = OllamaCliConfig(onboarding_complete=True)
        with patch("ollama_cmd.onboarding.get_config", return_value=cfg):
            assert needs_onboarding() is False

    def test_needs_onboarding_reads_from_config_json(self, tmp_path: Path) -> None:
        """Onboarding flag persists via config.json round-trip."""
        cfg = OllamaCliConfig(onboarding_complete=True)
        config_path = tmp_path / "config.json"
        save_config(cfg, config_path)

        with open(config_path) as f:
            data = json.load(f)
        assert data["onboarding_complete"] is True


class TestRunOnboarding:
    """Verify the onboarding wizard populates config correctly."""

    def test_run_onboarding_sets_provider_and_model(self, tmp_path: Path) -> None:
        """Wizard saves provider, model, and marks complete."""
        cfg = OllamaCliConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path) as mock_save,
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
        ):
            # Simulate user choosing gemini provider, default model, skip api key
            mock_ask.side_effect = [
                "gemini",      # provider choice
                "",            # API key (empty)
                "gemini-2.5-flash",  # model
            ]
            result = run_onboarding()

        assert result.provider == "gemini"
        assert result.ollama_model == "gemini-2.5-flash"
        assert result.onboarding_complete is True
        mock_save.assert_called_once()

    def test_run_onboarding_ollama_asks_host(self, tmp_path: Path) -> None:
        """When ollama provider is chosen, wizard also asks for host URL."""
        cfg = OllamaCliConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
        ):
            mock_ask.side_effect = [
                "ollama",                    # provider
                "llama3.2",                  # model
                "http://localhost:11434",     # host
            ]
            result = run_onboarding()

        assert result.provider == "ollama"
        assert result.ollama_model == "llama3.2"
        assert result.ollama_host == "http://localhost:11434"
        assert result.onboarding_complete is True

    def test_run_onboarding_cloud_provider_sets_api_key(self, tmp_path: Path) -> None:
        """When a cloud provider is chosen, API key is stored in config."""
        cfg = OllamaCliConfig()
        config_path = tmp_path / "config.json"

        with (
            patch("ollama_cmd.onboarding.get_config", return_value=cfg),
            patch("ollama_cmd.onboarding.save_config", return_value=config_path),
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("ollama_cmd.onboarding.console"),
        ):
            mock_ask.side_effect = [
                "claude",          # provider
                "sk-test-key",     # API key
                "claude-sonnet-4-20250514",  # model
            ]
            result = run_onboarding()

        assert result.provider == "claude"
        assert result.anthropic_api_key == "sk-test-key"
        assert result.onboarding_complete is True
