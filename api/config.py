#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Configuration management for ollama-cli.

Loads settings from environment variables (via .env) and overlays
from .ollama/config.json if it exists. Provides a singleton accessor.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class OllamaCliConfig:
    """Central configuration for the CLI."""

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    provider: str = "ollama"
    context_length: int = 4096
    auto_compact: bool = True
    compact_threshold: float = 0.85
    cloud_host: str = ""
    cloud_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    hooks_enabled: bool = True
    output_format: str = "text"
    allowed_tools: list[str] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bool_from_env(value: str | None, default: bool) -> bool:
    """Parse a boolean from an environment variable string."""
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _int_from_env(value: str | None, default: int) -> int:
    """Parse an int from an environment variable string."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_from_env(value: str | None, default: float) -> float:
    """Parse a float from an environment variable string."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------


def load_config(env_path: str | Path | None = None, config_json_path: str | Path | None = None) -> OllamaCliConfig:
    """Load configuration from environment variables, then overlay from config.json.

    Parameters
    ----------
    env_path:
        Path to a .env file.  Defaults to ``<cwd>/.env``.
    config_json_path:
        Path to a JSON override file.  Defaults to ``<cwd>/.ollama/config.json``.
    """
    # Load .env
    if env_path is None:
        # Try ollama-cli directory first, then cwd
        candidates = [
            Path(__file__).resolve().parent.parent / ".env",
            Path.cwd() / ".env",
        ]
        for candidate in candidates:
            if candidate.exists():
                load_dotenv(candidate)
                break
    else:
        load_dotenv(env_path)

    # Build config from env vars
    cfg = OllamaCliConfig(
        ollama_host=os.getenv("OLLAMA_HOST", OllamaCliConfig.ollama_host),
        ollama_model=os.getenv("OLLAMA_MODEL", OllamaCliConfig.ollama_model),
        provider=os.getenv("OLLAMA_CLI_PROVIDER", OllamaCliConfig.provider),
        context_length=_int_from_env(os.getenv("OLLAMA_CONTEXT_LENGTH"), OllamaCliConfig.context_length),
        auto_compact=_bool_from_env(os.getenv("AUTO_COMPACT"), OllamaCliConfig.auto_compact),
        compact_threshold=_float_from_env(os.getenv("COMPACT_THRESHOLD"), OllamaCliConfig.compact_threshold),
        cloud_host=os.getenv("OLLAMA_CLOUD_HOST", OllamaCliConfig.cloud_host),
        cloud_api_key=os.getenv("OLLAMA_CLOUD_API_KEY", OllamaCliConfig.cloud_api_key),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", OllamaCliConfig.anthropic_api_key),
        gemini_api_key=os.getenv("GEMINI_API_KEY", OllamaCliConfig.gemini_api_key),
        openai_api_key=os.getenv("OPENAI_API_KEY", OllamaCliConfig.openai_api_key),
        hooks_enabled=_bool_from_env(os.getenv("HOOKS_ENABLED"), OllamaCliConfig.hooks_enabled),
    )

    # Overlay from JSON config file if it exists
    if config_json_path is None:
        config_json_path = Path(__file__).resolve().parent.parent / ".ollama" / "config.json"
    else:
        config_json_path = Path(config_json_path)

    if config_json_path.exists():
        try:
            with open(config_json_path) as f:
                overrides = json.load(f)
            for key, value in overrides.items():
                if hasattr(cfg, key):
                    expected_type = type(getattr(cfg, key))
                    try:
                        setattr(cfg, key, expected_type(value))
                    except (TypeError, ValueError):
                        pass  # skip malformed overrides
        except (json.JSONDecodeError, OSError):
            pass  # ignore broken config files

    return cfg


def save_config(config: OllamaCliConfig, path: str | Path | None = None) -> Path:
    """Save the config to a JSON file.

    Parameters
    ----------
    config:
        The configuration to persist.
    path:
        Destination path.  Defaults to ``<script_dir>/../.ollama/config.json``.

    Returns
    -------
    Path to the written file.
    """
    if path is None:
        path = Path(__file__).resolve().parent.parent / ".ollama" / "config.json"
    else:
        path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    # Exclude sensitive and runtime-only keys from the persisted file
    data = asdict(config)
    excluded_keys = {"cloud_api_key", "anthropic_api_key", "gemini_api_key", "openai_api_key", "allowed_tools"}
    for key in excluded_keys:
        data.pop(key, None)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return path


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_config_instance: OllamaCliConfig | None = None


def get_config() -> OllamaCliConfig:
    """Return the singleton config, loading it on first access."""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cfg = load_config()
    print(json.dumps(asdict(cfg), indent=2))
