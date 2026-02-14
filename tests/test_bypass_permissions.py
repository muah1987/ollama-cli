"""Tests for permissions/bypass.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestBypassPermissions:
    def test_init_enabled(self):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=True)
        bp = BypassPermissions(cfg)
        assert bp.enabled is True
        assert bp.should_bypass() is True

    def test_init_disabled(self):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=False)
        bp = BypassPermissions(cfg)
        assert bp.enabled is False
        assert bp.should_bypass() is False

    def test_bypass_confirm_when_enabled(self, capsys):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=True)
        bp = BypassPermissions(cfg)
        result = bp.bypass_confirm("Delete all?", default=True)
        assert result is True
        out = capsys.readouterr().out
        assert "Bypassing confirmation" in out

    def test_bypass_confirm_when_disabled(self):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=False)
        bp = BypassPermissions(cfg)
        result = bp.bypass_confirm("Delete all?", default=False)
        assert result is False

    def test_bypass_input_when_enabled(self, capsys):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=True)
        bp = BypassPermissions(cfg)
        result = bp.bypass_input("Enter name:", default="auto")
        assert result == "auto"
        out = capsys.readouterr().out
        assert "Bypassing input" in out

    def test_bypass_input_when_disabled(self):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=False)
        bp = BypassPermissions(cfg)
        result = bp.bypass_input("Enter name:", default="auto")
        assert result == "auto"

    def test_bypass_choice_when_enabled(self, capsys):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=True)
        bp = BypassPermissions(cfg)
        result = bp.bypass_choice("Pick one:", choices=["a", "b", "c"], default="b")
        assert result == "b"
        out = capsys.readouterr().out
        assert "Bypassing choice" in out

    def test_bypass_choice_when_disabled(self):
        from permissions.bypass import BypassPermissions

        cfg = MagicMock(bypass_permissions=False)
        bp = BypassPermissions(cfg)
        result = bp.bypass_choice("Pick one:", choices=["a", "b"], default="a")
        assert result == "a"


class TestGetBypassManager:
    def test_get_bypass_manager_first_init(self):
        import permissions.bypass as mod

        mod._bypass_instance = None  # Reset singleton
        cfg = MagicMock(bypass_permissions=False)
        manager = mod.get_bypass_manager(cfg)
        assert manager is not None
        assert manager.should_bypass() is False
        mod._bypass_instance = None  # Cleanup

    def test_get_bypass_manager_no_config_raises(self):
        import permissions.bypass as mod

        mod._bypass_instance = None
        with pytest.raises(ValueError, match="Configuration required"):
            mod.get_bypass_manager(None)
        mod._bypass_instance = None

    def test_get_bypass_manager_reuses_instance(self):
        import permissions.bypass as mod

        mod._bypass_instance = None
        cfg = MagicMock(bypass_permissions=True)
        m1 = mod.get_bypass_manager(cfg)
        m2 = mod.get_bypass_manager()
        assert m1 is m2
        mod._bypass_instance = None


class TestShouldBypassPermissions:
    @patch("api.config.get_config")
    def test_should_bypass_permissions(self, mock_cfg):
        import permissions.bypass as mod

        mod._bypass_instance = None
        mock_cfg.return_value = MagicMock(bypass_permissions=True)
        result = mod.should_bypass_permissions()
        assert result is True
        mod._bypass_instance = None

    @patch("api.config.get_config")
    def test_should_not_bypass(self, mock_cfg):
        import permissions.bypass as mod

        mod._bypass_instance = None
        mock_cfg.return_value = MagicMock(bypass_permissions=False)
        result = mod.should_bypass_permissions()
        assert result is False
        mod._bypass_instance = None


class TestBypassConfirmPrompt:
    @patch("api.config.get_config")
    def test_bypass_confirm_prompt(self, mock_cfg):
        import permissions.bypass as mod

        mod._bypass_instance = None
        mock_cfg.return_value = MagicMock(bypass_permissions=True)
        result = mod.bypass_confirm_prompt("OK?", default=True)
        assert result is True
        mod._bypass_instance = None


class TestBypassInputPrompt:
    @patch("api.config.get_config")
    def test_bypass_input_prompt(self, mock_cfg):
        import permissions.bypass as mod

        mod._bypass_instance = None
        mock_cfg.return_value = MagicMock(bypass_permissions=True)
        result = mod.bypass_input_prompt("Name?", default="test")
        assert result == "test"
        mod._bypass_instance = None
