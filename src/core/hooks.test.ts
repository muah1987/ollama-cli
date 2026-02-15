import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import { writeFile, mkdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { HookRunner } from "./hooks.js";

describe("HookRunner", () => {
  const testDir = join(process.cwd(), ".test-hooks");
  const settingsPath = join(testDir, "settings.json");

  before(async () => {
    await mkdir(testDir, { recursive: true });
  });

  after(async () => {
    await rm(testDir, { recursive: true, force: true });
  });

  it("creates a disabled hook runner by default", () => {
    const runner = new HookRunner();
    assert.equal(runner.isEnabled(), false);
  });

  it("loads hook configuration from settings file", async () => {
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

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();
    assert.equal(runner.isEnabled(), true);
  });

  it("handles missing settings file gracefully", async () => {
    const runner = new HookRunner(join(testDir, "nonexistent.json"));
    await runner.load();
    assert.equal(runner.isEnabled(), false);
  });

  it("handles settings file without hooks", async () => {
    const settings = {};
    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();
    assert.equal(runner.isEnabled(), false);
  });

  it("runs a hook command successfully", async () => {
    const settings = {
      hooks: {
        UserPromptSubmit: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "echo 'User prompt received'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    const results = await runner.runHook("UserPromptSubmit", {
      session_id: "test-123",
      message: "Hello",
    });

    assert.equal(results.length, 1);
    assert.ok(results[0].success);
    assert.ok(results[0].stdout.includes("User prompt received"));
  });

  it("handles hook command timeout", async () => {
    const settings = {
      hooks: {
        SessionStart: [
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

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    const results = await runner.runHook("SessionStart", {
      session_id: "test-123",
    }, 1); // 1 second timeout

    assert.equal(results.length, 1);
    assert.equal(results[0].success, false);
  });

  it("matches hook patterns", async () => {
    const settings = {
      hooks: {
        PreToolUse: [
          {
            matcher: "file_read",
            hooks: [
              {
                type: "command",
                command: "echo 'Reading file'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    // Should run for matching tool
    const results1 = await runner.runHook("PreToolUse", {
      tool_name: "file_read",
    });
    assert.equal(results1.length, 1);
    assert.ok(results1[0].success);
    assert.ok(results1[0].stdout.includes("Reading file"));

    // Should not run for non-matching tool
    const results2 = await runner.runHook("PreToolUse", {
      tool_name: "file_write",
    });
    assert.equal(results2.length, 0);
  });

  it("supports both camelCase and snake_case tool names", async () => {
    const settings = {
      hooks: {
        PreToolUse: [
          {
            matcher: "file_read",
            hooks: [
              {
                type: "command",
                command: "echo 'Reading file'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    // Should work with snake_case
    const results1 = await runner.runHook("PreToolUse", {
      tool_name: "file_read",
    });
    assert.equal(results1.length, 1);
    assert.ok(results1[0].success);

    // Should work with camelCase
    const results2 = await runner.runHook("PreToolUse", {
      toolName: "file_read",
    });
    assert.equal(results2.length, 1);
    assert.ok(results2[0].success);
  });

  it("passes payload via stdin", async () => {
    const settings = {
      hooks: {
        UserPromptSubmit: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "cat",
              },
            ],
          },
        ],
      },
    };

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    const payload = {
      session_id: "test-456",
      message: "Test message",
    };

    const results = await runner.runHook("UserPromptSubmit", payload);
    assert.equal(results.length, 1);
    assert.ok(results[0].success);
    
    // The hook command (cat) should echo back the JSON payload
    const outputObj = JSON.parse(results[0].stdout);
    assert.equal(outputObj.session_id, "test-456");
    assert.equal(outputObj.message, "Test message");
  });

  it("parses JSON from hook stdout", async () => {
    const settings = {
      hooks: {
        PermissionRequest: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "echo '{\"allow\": true}'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    const results = await runner.runHook("PermissionRequest", {
      tool: "file_read",
    });

    assert.equal(results.length, 1);
    assert.ok(results[0].success);
    assert.ok(results[0].parsed);
    assert.equal(results[0].parsed.allow, true);
  });

  it("handles hook command errors", async () => {
    const settings = {
      hooks: {
        SessionStart: [
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

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    const results = await runner.runHook("SessionStart", {
      session_id: "test-789",
    });

    assert.equal(results.length, 1);
    assert.equal(results[0].success, false);
    assert.equal(results[0].returnCode, 1);
  });

  it("runs multiple hooks for the same event", async () => {
    const settings = {
      hooks: {
        SessionEnd: [
          {
            matcher: "",
            hooks: [
              {
                type: "command",
                command: "echo 'Hook 1'",
              },
              {
                type: "command",
                command: "echo 'Hook 2'",
              },
            ],
          },
        ],
      },
    };

    await writeFile(settingsPath, JSON.stringify(settings), "utf-8");
    const runner = new HookRunner(settingsPath);
    await runner.load();

    const results = await runner.runHook("SessionEnd", {
      session_id: "test-multi",
    });

    assert.equal(results.length, 2);
    assert.ok(results[0].success);
    assert.ok(results[1].success);
    assert.ok(results[0].stdout.includes("Hook 1") || results[0].stdout.includes("Hook 2"));
    assert.ok(results[1].stdout.includes("Hook 1") || results[1].stdout.includes("Hook 2"));
  });
});
