#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "httpx",
#     "rich",
# ]
# ///
"""
ollama-cli -- Full-featured AI coding assistant powered by Ollama.

Main CLI entry point.  Provides subcommands for chatting, running prompts,
listing models, pulling models, and managing configuration.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

# ---------------------------------------------------------------------------