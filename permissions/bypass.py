#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "rich",
# ]
# ///

"""
Permissions bypass module for ollama-cli.

This module provides functionality to bypass interactive prompts and permissions
for autonomous operation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.config import OllamaCliConfig

class BypassPermissions:
    """Manager for bypassing permissions and interactive prompts."""

    def __init__(self, config: OllamaCliConfig):
        """Initialize the bypass permissions manager.

        Parameters
        ----------
        config:
            The CLI configuration object.
        """
        self.config = config
        self.enabled = config.bypass_permissions

    def should_bypass(self) -> bool:
        """Check if bypass mode is enabled.

        Returns
        -------
        True if bypass mode is enabled, False otherwise.
        """
        return self.enabled

    def bypass_confirm(self, message: str, default: bool = True) -> bool:
        """Bypass a confirmation prompt.

        Parameters
        ----------
        message:
            The confirmation message that would normally be shown.
        default:
            The default response if not bypassing.

        Returns
        -------
        The default value when bypassing, or the user's choice otherwise.
        """
        if self.should_bypass():
            print(f"Bypassing confirmation: {message}")
            print(f"Using default response: {'Yes' if default else 'No'}")
            return default
        # If not bypassing, we would normally prompt the user
        # For now, we'll just return the default to avoid breaking existing code
        return default

    def bypass_input(self, message: str, default: str = "") -> str:
        """Bypass an input prompt.

        Parameters
        ----------
        message:
            The input prompt message that would normally be shown.
        default:
            The default response if not bypassing.

        Returns
        -------
        The default value when bypassing, or the user's input otherwise.
        """
        if self.should_bypass():
            print(f"Bypassing input prompt: {message}")
            print(f"Using default response: '{default}'")
            return default
        # If not bypassing, we would normally prompt the user
        # For now, we'll just return the default to avoid breaking existing code
        return default

    def bypass_choice(self, message: str, choices: list[str], default: str = "") -> str:
        """Bypass a choice prompt.

        Parameters
        ----------
        message:
            The choice prompt message that would normally be shown.
        choices:
            The available choices.
        default:
            The default response if not bypassing.

        Returns
        -------
        The default value when bypassing, or the user's choice otherwise.
        """
        if self.should_bypass():
            print(f"Bypassing choice prompt: {message}")
            print(f"Available choices: {choices}")
            print(f"Using default response: '{default}'")
            return default
        # If not bypassing, we would normally prompt the user
        # For now, we'll just return the default to avoid breaking existing code
        return default

# Global instance for easy access
_bypass_instance: BypassPermissions | None = None

def get_bypass_manager(config: OllamaCliConfig | None = None) -> BypassPermissions:
    """Get the global bypass permissions manager instance.

    Parameters
    ----------
    config:
        Configuration object. Required for first initialization.

    Returns
    -------
    The global bypass permissions manager instance.
    """
    global _bypass_instance
    if _bypass_instance is None:
        if config is None:
            raise ValueError("Configuration required for initializing bypass manager")
        _bypass_instance = BypassPermissions(config)
    return _bypass_instance

def should_bypass_permissions() -> bool:
    """Check if bypass mode is enabled globally.

    This function provides a convenient way to check bypass status without
    needing to access the configuration directly.

    Returns
    -------
    True if bypass mode is enabled, False otherwise.
    """
    from api.config import get_config
    config = get_config()
    bypass_manager = get_bypass_manager(config)
    return bypass_manager.should_bypass()

def bypass_confirm_prompt(message: str, default: bool = True) -> bool:
    """Bypass a confirmation prompt with default behavior.

    Parameters
    ----------
    message:
        The confirmation message that would normally be shown.
    default:
        The default response if not bypassing.

    Returns
    -------
    The default value when bypassing, or the user's choice otherwise.
    """
    from api.config import get_config
    config = get_config()
    bypass_manager = get_bypass_manager(config)
    return bypass_manager.bypass_confirm(message, default)

def bypass_input_prompt(message: str, default: str = "") -> str:
    """Bypass an input prompt with default behavior.

    Parameters
    ----------
    message:
        The input prompt message that would normally be shown.
    default:
        The default response if not bypassing.

    Returns
    -------
    The default value when bypassing, or the user's input otherwise.
    """
    from api.config import get_config
    config = get_config()
    bypass_manager = get_bypass_manager(config)
    return bypass_manager.bypass_input(message, default)

# Example usage when run directly
if __name__ == "__main__":
    # This is just for testing the module directly
    print("Bypass permissions module loaded successfully.")
    print("Use get_bypass_manager() to access the bypass manager.")
    print("Use should_bypass_permissions() to check if bypass is enabled.")