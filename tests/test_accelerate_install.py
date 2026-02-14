"""Tests for ollama_cmd/accelerate.py and ollama_cmd/install.py."""

from __future__ import annotations

import argparse
from unittest.mock import patch



class TestAccelerateModule:
    def test_cmd_accelerate_check(self):
        from ollama_cmd.accelerate import cmd_accelerate_check
        args = argparse.Namespace()
        cmd_accelerate_check(args)  # Should print status

    def test_cmd_accelerate(self):
        from ollama_cmd.accelerate import cmd_accelerate
        args = argparse.Namespace()
        cmd_accelerate(args)


class TestInstallModule:
    @patch("shutil.which")
    def test_check_ollama_installed(self, mock_which):
        from ollama_cmd.install import cmd_check_ollama
        mock_which.return_value = "/usr/bin/ollama"
        args = argparse.Namespace()
        cmd_check_ollama(args)

    @patch("shutil.which")
    def test_check_ollama_not_installed(self, mock_which):
        from ollama_cmd.install import cmd_check_ollama
        mock_which.return_value = None
        args = argparse.Namespace()
        cmd_check_ollama(args)

    def test_cmd_install(self):
        from ollama_cmd.install import cmd_install
        args = argparse.Namespace()
        cmd_install(args)
