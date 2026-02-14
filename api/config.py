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
    ollama_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    hf_token: str = ""
    gh_token: str = ""
    hooks_enabled: bool = True
    output_format: str = "text"
    allowed_tools: list[str] | None = None
    agent_models: dict[str, dict[str, str]] | None = None
    onboarding_complete: bool = False
    intent_enabled: bool = True
    intent_confidence_threshold: float = 0.7
    intent_llm_fallback: bool = False
    intent_show_detection: bool = True
    intent_default_agent_type: str | None = None
    tui_theme: str = "dark"
    tui_sidebar_visible: bool = True
    tui_show_timestamps: bool = True
    tui_auto_scroll: bool = True
    planning_mode: bool = False
    work_mode: bool = False
    bypass_permissions: bool = False


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
        ollama_api_key=os.getenv("OLLAMA_API_KEY", OllamaCliConfig.ollama_api_key),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", OllamaCliConfig.anthropic_api_key),
        gemini_api_key=os.getenv("GEMINI_API_KEY", OllamaCliConfig.gemini_api_key),
        openai_api_key=os.getenv("OPENAI_API_KEY", OllamaCliConfig.openai_api_key),
        hf_token=os.getenv("HF_TOKEN", OllamaCliConfig.hf_token),
        gh_token=os.getenv("GH_TOKEN", OllamaCliConfig.gh_token),
        hooks_enabled=_bool_from_env(os.getenv("HOOKS_ENABLED"), OllamaCliConfig.hooks_enabled),
        intent_enabled=_bool_from_env(os.getenv("OLLAMA_CLI_INTENT_ENABLED"), OllamaCliConfig.intent_enabled),
        intent_confidence_threshold=_float_from_env(
            os.getenv("OLLAMA_CLI_INTENT_THRESHOLD"), OllamaCliConfig.intent_confidence_threshold
        ),
        intent_llm_fallback=_bool_from_env(
            os.getenv("OLLAMA_CLI_INTENT_LLM_FALLBACK"), OllamaCliConfig.intent_llm_fallback
        ),
        intent_show_detection=_bool_from_env(os.getenv("OLLAMA_CLI_INTENT_SHOW"), OllamaCliConfig.intent_show_detection),
        intent_default_agent_type=os.getenv("OLLAMA_CLI_INTENT_DEFAULT_AGENT"),
        tui_theme=os.getenv("OLLAMA_CLI_TUI_THEME", OllamaCliConfig.tui_theme),
        tui_sidebar_visible=_bool_from_env(os.getenv("OLLAMA_CLI_TUI_SIDEBAR"), OllamaCliConfig.tui_sidebar_visible),
        tui_show_timestamps=_bool_from_env(
            os.getenv("OLLAMA_CLI_TUI_TIMESTAMPS"), OllamaCliConfig.tui_show_timestamps
        ),
        tui_auto_scroll=_bool_from_env(os.getenv("OLLAMA_CLI_TUI_AUTOSCROLL"), OllamaCliConfig.tui_auto_scroll),
        planning_mode=_bool_from_env(os.getenv("OLLAMA_CLI_PLANNING_MODE"), OllamaCliConfig.planning_mode),
        work_mode=_bool_from_env(os.getenv("OLLAMA_CLI_WORK_MODE"), OllamaCliConfig.work_mode),
        bypass_permissions=_bool_from_env(os.getenv("OLLAMA_CLI_BYPASS_PERMISSIONS"), OllamaCliConfig.bypass_permissions),
    )

    # Overlay from JSON config file if it exists
    if config_json_path is None:
        # Try CWD first, then source directory (so per-project config takes priority)
        candidates = [
            Path.cwd() / ".ollama" / "config.json",
            Path(__file__).resolve().parent.parent / ".ollama" / "config.json",
        ]
        config_json_path = None
        for candidate in candidates:
            if candidate.exists():
                config_json_path = candidate
                break
        if config_json_path is None:
            # Use CWD as default save location for new configs
            config_json_path = Path.cwd() / ".ollama" / "config.json"
    else:
        config_json_path = Path(config_json_path)

    if config_json_path.exists():
        try:
            with open(config_json_path) as f:
                overrides = json.load(f)
            for key, value in overrides.items():
                if hasattr(cfg, key):
                    current = getattr(cfg, key)
                    if current is None and key == "agent_models" and isinstance(value, dict):
                        setattr(cfg, key, value)
                    elif current is not None:
                        expected_type = type(current)
                        try:
                            setattr(cfg, key, expected_type(value))
                        except (TypeError, ValueError):
                            pass  # skip malformed overrides
        except (json.JSONDecodeError, OSError):
            pass  # ignore broken config files

    # Load agent_models and intent_classifier from settings.json
    settings_path = Path(__file__).resolve().parent.parent / ".ollama" / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                settings_data = json.load(f)

            # agent_models: only if not already set
            if cfg.agent_models is None:
                agent_models = settings_data.get("agent_models")
                if isinstance(agent_models, dict):
                    cfg.agent_models = agent_models

            # intent_classifier: settings.json values are used as defaults,
            # but env vars (already loaded above) take precedence.
            intent_cfg = settings_data.get("intent_classifier")
            if isinstance(intent_cfg, dict):
                # Only apply settings.json value when the env var was NOT set
                if os.getenv("OLLAMA_CLI_INTENT_ENABLED") is None and "enabled" in intent_cfg:
                    cfg.intent_enabled = bool(intent_cfg["enabled"])
                if os.getenv("OLLAMA_CLI_INTENT_THRESHOLD") is None and "confidence_threshold" in intent_cfg:
                    try:
                        cfg.intent_confidence_threshold = float(intent_cfg["confidence_threshold"])
                    except (TypeError, ValueError):
                        pass
                if os.getenv("OLLAMA_CLI_INTENT_LLM_FALLBACK") is None and "llm_fallback" in intent_cfg:
                    cfg.intent_llm_fallback = bool(intent_cfg["llm_fallback"])
                if os.getenv("OLLAMA_CLI_INTENT_SHOW") is None and "show_intent" in intent_cfg:
                    cfg.intent_show_detection = bool(intent_cfg["show_intent"])
                if os.getenv("OLLAMA_CLI_INTENT_DEFAULT_AGENT") is None and "default_agent_type" in intent_cfg:
                    val = intent_cfg["default_agent_type"]
                    cfg.intent_default_agent_type = str(val) if val is not None else None

            # tui: settings.json values are used as defaults,
            # but env vars (already loaded above) take precedence.
            tui_cfg = settings_data.get("tui")
            if isinstance(tui_cfg, dict):
                if os.getenv("OLLAMA_CLI_TUI_THEME") is None and "theme" in tui_cfg:
                    cfg.tui_theme = str(tui_cfg["theme"])
                if os.getenv("OLLAMA_CLI_TUI_SIDEBAR") is None and "sidebar_visible" in tui_cfg:
                    cfg.tui_sidebar_visible = bool(tui_cfg["sidebar_visible"])
                if os.getenv("OLLAMA_CLI_TUI_TIMESTAMPS") is None and "show_timestamps" in tui_cfg:
                    cfg.tui_show_timestamps = bool(tui_cfg["show_timestamps"])
                if os.getenv("OLLAMA_CLI_TUI_AUTOSCROLL") is None and "auto_scroll" in tui_cfg:
                    cfg.tui_auto_scroll = bool(tui_cfg["auto_scroll"])
        except (json.JSONDecodeError, OSError):
            pass

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
        # Prefer CWD for per-project config; fall back to source directory
        cwd_path = Path.cwd() / ".ollama" / "config.json"
        src_path = Path(__file__).resolve().parent.parent / ".ollama" / "config.json"
        if cwd_path.parent.exists() or not src_path.parent.exists():
            path = cwd_path
        else:
            path = src_path
    else:
        path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    # Exclude sensitive and runtime-only keys from the persisted file
    data = asdict(config)
    excluded_keys = {
        "cloud_api_key",
        "ollama_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "openai_api_key",
        "hf_token",
        "gh_token",
        "allowed_tools",
    }
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
