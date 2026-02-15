import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { writeFile, unlink, mkdir, chmod } from "node:fs/promises";
import { join } from "node:path";
import { HookRunner } from "./hooks.js";

describe("HookRunner", () => {
  const testHookDir = "/tmp/qarin-test-hooks";
  const testSettingsPath = join(testHookDir, "settings.json");

  beforeEach(async () => {
    await mkdir(testHookDir, { recursive: true });
  });

  afterEach(async () => {
    // Clean up test files
    try {
      await unlink(testSettingsPath).catch(() => {});
      await unlink(join(testHookDir, "test-hook.sh")).catch(() => {});
    } catch {
      // Ignore cleanup errors
    }
  });

  it("initializes with empty hooks when no settings file exists", async () => {
    const runner = new HookRunner("/nonexistent/settings.json");
    await runner.load();
    assert.equal(runner.isEnabled(), false); // No hooks loaded
  });

  it("loads hooks from settings.json", async () => {
    const settings = {
      hooks: {
        SessionStart: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "echo 'Session started'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    assert.equal(runner.isEnabled(), true);
  });

  it("executes a simple hook command", async () => {
    const settings = {
      hooks: {
        SessionStart: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "echo 'test output'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    const results = await runner.runHook("SessionStart", { test: "data" });
    assert.ok(results.length > 0);
    assert.equal(results[0].success, true);
    assert.ok(results[0].stdout.includes("test output"));
  });

  it("receives payload via stdin", async () => {
    const hookScript = join(testHookDir, "test-hook.sh");
    await writeFile(
      hookScript,
      '#!/bin/sh\nread input\necho "$input"',
      "utf-8",
    );
    await chmod(hookScript, 0o755);

    const settings = {
      hooks: {
        UserPromptSubmit: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: hookScript,
              },
            ],
          },
        ],
      },
    };

    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    const payload = { message: "test message", session_id: "123" };
    const results = await runner.runHook("UserPromptSubmit", payload);

    assert.ok(results.length > 0);
    assert.equal(results[0].success, true);
    // The hook should receive the JSON payload
    assert.ok(results[0].stdout.includes("test message"));
  });

  it("supports both camelCase and snake_case for toolName", async () => {
    const settings = {
      hooks: {
        PreToolUse: [
          {
            matcher: "file_read",
            hooks: [
              {
                type: "command",
                command: "echo 'hook matched'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    // Test with snake_case
    let results = await runner.runHook("PreToolUse", {
      tool_name: "file_read",
    });
    assert.ok(results.length > 0);
    assert.equal(results[0].success, true);

    // Test with camelCase
    results = await runner.runHook("PreToolUse", { toolName: "file_read" });
    assert.ok(results.length > 0);
    assert.equal(results[0].success, true);
  });

  it("filters hooks by matcher", async () => {
    const settings = {
      hooks: {
        PreToolUse: [
          {
            matcher: "file_read",
            hooks: [
              {
                type: "command",
                command: "echo 'file operation'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    // Should match
    let results = await runner.runHook("PreToolUse", {
      tool_name: "file_read",
    });
    assert.ok(results.length > 0);
    assert.equal(results[0].success, true);
    assert.ok(results[0].stdout.includes("file operation"));

    // Should not match - returns empty array
    results = await runner.runHook("PreToolUse", { tool_name: "shell_exec" });
    assert.equal(results.length, 0);
  });

  it("handles hook command failures", async () => {
    const settings = {
      hooks: {
        SessionEnd: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "exit 1",
              },
            ],
          },
        ],
      },
    };

    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    const results = await runner.runHook("SessionEnd", {});
    assert.ok(results.length > 0);
    assert.equal(results[0].success, false);
    assert.ok(results[0].returnCode !== 0);
  });

  it("handles hook timeout", async () => {
    const settings = {
      hooks: {
        Stop: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "sleep 10",
              },
            ],
          },
        ],
      },
    };

    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    const results = await runner.runHook("Stop", {}, 1); // 1 second timeout
    assert.ok(results.length > 0);
    assert.equal(results[0].success, false);
    // Timeout could set killed flag or return an error code
    assert.ok(results[0].killed || results[0].returnCode !== 0);
  });

  it("returns empty array when no hooks are registered", async () => {
    const settings = { hooks: {} };
    await writeFile(testSettingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(testSettingsPath);
    await runner.load();

    const results = await runner.runHook("SessionStart", {});
    assert.equal(results.length, 0);
  });
});
