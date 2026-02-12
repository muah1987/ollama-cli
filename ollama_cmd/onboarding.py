"""First-time interactive onboarding wizard for ollama-cli.

Runs once after installation to help the user choose a provider, enter API
keys (if needed), and pick a default model.  Saves the result to
``.ollama/config.json`` with ``onboarding_complete: true`` so it never runs
again unless the user deletes the config.
"""

from __future__ import annotations

import asyncio
import os

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from api.config import OllamaCliConfig, get_config, save_config

console = Console()

# Providers and their required environment-variable / config key
_PROVIDERS: dict[str, str | None] = {
    "ollama": "ollama_api_key",  # optional key for cloud/authenticated Ollama
    "claude": "anthropic_api_key",
    "gemini": "gemini_api_key",
    "codex": "openai_api_key",
    "hf": "hf_token",
}

_PROVIDER_ENV_MAP: dict[str, str] = {
    "ollama_api_key": "OLLAMA_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "hf_token": "HF_TOKEN",
}

_DEFAULT_MODELS: dict[str, str] = {
    "ollama": "llama3.2",
    "claude": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.5-flash",
    "codex": "gpt-4.1",
    "hf": "mistralai/Mistral-7B-Instruct-v0.2",
}


def _fetch_provider_models(provider_name: str) -> list[str]:
    """Fetch available models from a cloud provider.

    Returns a list of model identifiers, or an empty list on failure.
    """
    from api.provider_router import ProviderRouter

    try:
        router = ProviderRouter()
        provider = router.get_provider(provider_name)
        models = asyncio.run(provider.list_models())
        asyncio.run(provider.close())
        return models
    except Exception:
        return []


def needs_onboarding() -> bool:
    """Return True when first-time setup has not been completed."""
    cfg = get_config()
    return not cfg.onboarding_complete


def run_onboarding() -> OllamaCliConfig:
    """Run the interactive first-time setup wizard.

    Returns the updated :class:`OllamaCliConfig` (already persisted).
    """
    cfg = get_config()

    console.print()
    console.print(
        Panel(
            "[bold cyan]Welcome to ollama-cli![/bold cyan]\n\n"
            "Let's get you set up. This wizard runs only once.\n"
            "You can change these settings later with [bold]/config[/bold] "
            "or by editing [bold].ollama/config.json[/bold].",
            title="First-Time Setup",
            border_style="cyan",
        )
    )
    console.print()

    # --- 1. Choose provider -------------------------------------------------
    provider_list = list(_PROVIDERS.keys())
    console.print("[bold]Available providers:[/bold]")
    for i, prov in enumerate(provider_list, 1):
        label = "[green](local or cloud)[/green]" if prov == "ollama" else ""
        console.print(f"  {i}. {prov}  {label}")
    console.print()

    choices_display = "/".join(provider_list)
    while True:
        raw = Prompt.ask(
            f"Choose a provider [{choices_display}]",
            default="ollama",
        )
        # Accept a 1-based index as well as the provider name.
        if raw.isdigit() and 1 <= int(raw) <= len(provider_list):
            provider_choice = provider_list[int(raw) - 1]
            break
        if raw in provider_list:
            provider_choice = raw
            break
        console.print(f"[prompt.invalid]Please enter a provider name or number (1-{len(provider_list)})")
    cfg.provider = provider_choice

    # --- 2. Ollama host (for ollama provider, asked first so model fetch
    #        can reach the correct server) -----------------------------------
    if provider_choice == "ollama":
        host = Prompt.ask(
            "Ollama host URL",
            default=cfg.ollama_host or "http://localhost:11434",
        )
        cfg.ollama_host = host

    # --- 3. API key (if cloud provider) -------------------------------------
    key_field = _PROVIDERS.get(provider_choice)
    if key_field is not None:
        current_key = getattr(cfg, key_field, "")
        if current_key:
            console.print(f"[green]API key for {provider_choice} already set from environment.[/green]")
        else:
            env_name = _PROVIDER_ENV_MAP.get(key_field, key_field.upper())
            key_label = (
                f"Enter your {provider_choice} API key, or press Enter to skip (env: {env_name})"
                if provider_choice == "ollama"
                else f"Enter your {provider_choice} API key (env: {env_name})"
            )
            api_key = Prompt.ask(
                key_label,
                password=True,
                default="",
            )
            if api_key:
                setattr(cfg, key_field, api_key)
                os.environ[env_name] = api_key

    # --- 4. Choose model ----------------------------------------------------
    default_model = _DEFAULT_MODELS.get(provider_choice, "llama3.2")

    # For cloud providers, try to fetch available models automatically.
    fetched_models: list[str] = []
    if key_field is not None:
        api_key_value = getattr(cfg, key_field, "")
        if api_key_value:
            console.print("\n[dim]Fetching available models…[/dim]")
            fetched_models = _fetch_provider_models(provider_choice)

    if fetched_models:
        console.print(f"\n[bold]Available {provider_choice} models:[/bold]")
        for i, m in enumerate(fetched_models, 1):
            marker = " [green](default)[/green]" if m == default_model else ""
            console.print(f"  {i}. {m}{marker}")
        console.print()

        while True:
            raw_model = Prompt.ask("Choose a model (name or number)", default=default_model)
            if raw_model.isdigit() and 1 <= int(raw_model) <= len(fetched_models):
                model = fetched_models[int(raw_model) - 1]
                break
            if raw_model in fetched_models or raw_model == default_model:
                model = raw_model
                break
            # Allow any free-form model name as well
            if raw_model:
                model = raw_model
                break
            console.print("[prompt.invalid]Please enter a model name or number")
    else:
        model = Prompt.ask(
            "Default model",
            default=default_model,
        )
    cfg.ollama_model = model

    # --- 5. Mark complete & save --------------------------------------------
    cfg.onboarding_complete = True
    saved_path = save_config(cfg)

    console.print()
    console.print(
        Panel(
            f"[bold green]Setup complete![/bold green]\n\n"
            f"  Provider : [cyan]{cfg.provider}[/cyan]\n"
            f"  Model    : [cyan]{cfg.ollama_model}[/cyan]\n"
            f"  Config   : [dim]{saved_path}[/dim]\n\n"
            "Type [bold]/help[/bold] inside the REPL for available commands.\n"
            "Run [bold]ollama-cli config set <key> <value>[/bold] to change settings later.",
            title="Ready",
            border_style="green",
        )
    )
    console.print()

    return cfg
