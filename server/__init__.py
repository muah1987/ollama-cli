"""Server package -- Server-related utilities and hooks.

This package contains:
- hook_runner: Executes hook scripts defined in settings.json
"""

from .hook_runner import HookResult, HookRunner, main

__all__ = ["HookRunner", "HookResult", "main"]
