"""Tests for server/hook_runner.py -- HookRunner and HookResult."""

from __future__ import annotations

import json


from server.hook_runner import HookResult, HookRunner


# ---------------------------------------------------------------------------
# HookResult
# ---------------------------------------------------------------------------


class TestHookResult:
    def test_defaults(self):
        r = HookResult(success=True)
        assert r.success is True
        assert r.stdout == ""
        assert r.stderr == ""
        assert r.return_code == 0
        assert r.parsed == {}
        assert r.error == ""

    def test_permission_decision(self):
        r = HookResult(success=True, parsed={"permissionDecision": "allow"})
        assert r.permission_decision == "allow"

    def test_permission_decision_missing(self):
        r = HookResult(success=True, parsed={})
        assert r.permission_decision is None

    def test_additional_context(self):
        r = HookResult(success=True, parsed={"additionalContext": "extra info"})
        assert r.additional_context == "extra info"

    def test_additional_context_missing(self):
        r = HookResult(success=True, parsed={})
        assert r.additional_context is None

    def test_updated_input(self):
        r = HookResult(success=True, parsed={"updatedInput": {"prompt": "new"}})
        assert r.updated_input == {"prompt": "new"}

    def test_updated_input_missing(self):
        r = HookResult(success=True, parsed={})
        assert r.updated_input is None


# ---------------------------------------------------------------------------
# HookRunner init & loading
# ---------------------------------------------------------------------------


class TestHookRunnerInit:
    def test_init_no_settings_file(self, tmp_path):
        runner = HookRunner(settings_path=tmp_path / "nonexistent.json")
        assert runner._hooks == {}
        assert runner.is_enabled() is False

    def test_init_with_valid_settings(self, tmp_path):
        settings = {
            "hooks": {
                "SessionStart": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "echo hello"}]}
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        assert runner.is_enabled() is True
        assert "SessionStart" in runner._hooks

    def test_init_with_invalid_json(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("{bad json", encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        assert runner._hooks == {}

    def test_init_empty_hooks(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text('{"hooks": {}}', encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        assert runner.is_enabled() is False


# ---------------------------------------------------------------------------
# HookRunner matching
# ---------------------------------------------------------------------------


class TestHookRunnerMatching:
    def test_empty_matcher_matches_all(self):
        assert HookRunner._matches("", {"tool_name": "anything"}) is True

    def test_exact_matcher(self):
        assert HookRunner._matches("file_read", {"tool_name": "file_read"}) is True

    def test_partial_matcher(self):
        assert HookRunner._matches("file", {"tool_name": "file_read"}) is True

    def test_no_match(self):
        assert HookRunner._matches("shell", {"tool_name": "file_read"}) is False


# ---------------------------------------------------------------------------
# HookRunner run_hook
# ---------------------------------------------------------------------------


class TestHookRunnerRunHook:
    def test_run_hook_no_hooks_for_event(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text('{"hooks": {}}', encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        results = runner.run_hook("SessionStart", {"session_id": "test"})
        assert results == []

    def test_run_hook_echo(self, tmp_path):
        settings = {
            "hooks": {
                "TestEvent": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "echo OK"}]}
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        results = runner.run_hook("TestEvent", {"data": "test"})
        assert len(results) == 1
        assert results[0].success is True
        assert "OK" in results[0].stdout

    def test_run_hook_json_output(self, tmp_path):
        cmd = """echo '{"permissionDecision": "allow"}'"""
        settings = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "", "hooks": [{"type": "command", "command": cmd}]}
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        results = runner.run_hook("PreToolUse", {"tool_name": "file_read"})
        assert len(results) == 1
        assert results[0].permission_decision == "allow"

    def test_run_hook_timeout(self, tmp_path):
        settings = {
            "hooks": {
                "Slow": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "sleep 60"}]}
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        results = runner.run_hook("Slow", {}, timeout=1)
        assert len(results) == 1
        assert results[0].success is False
        assert "timed out" in results[0].error

    def test_run_hook_failing_command(self, tmp_path):
        settings = {
            "hooks": {
                "Fail": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "exit 1"}]}
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        results = runner.run_hook("Fail", {})
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].return_code == 1

    def test_run_hook_skips_non_command_type(self, tmp_path):
        settings = {
            "hooks": {
                "Skip": [
                    {"matcher": "", "hooks": [{"type": "webhook", "url": "http://test"}]}
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        results = runner.run_hook("Skip", {})
        assert results == []

    def test_run_hook_matcher_filters(self, tmp_path):
        settings = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "shell", "hooks": [{"type": "command", "command": "echo matched"}]},
                    {"matcher": "file_read", "hooks": [{"type": "command", "command": "echo yes"}]},
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")
        runner = HookRunner(settings_path=settings_file)
        results = runner.run_hook("PreToolUse", {"tool_name": "file_read"})
        assert len(results) == 1
        assert "yes" in results[0].stdout
