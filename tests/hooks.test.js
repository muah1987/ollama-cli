/**
 * Unit tests for built-in hooks and permissions.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
    commitGuard,
    shouldAutoLint,
    shouldAutoTest,
    tokenAlert,
    HookPermissions,
    HookChain,
    getBuiltinHooks,
} from "../core/builtin-hooks.js";

describe("commitGuard", () => {
    it("blocks git push --force", () => {
        const result = commitGuard({ arguments: { command: "git push --force origin main" } });
        assert.equal(result.allow, false);
    });

    it("blocks rm -rf /", () => {
        const result = commitGuard({ arguments: { command: "rm -rf /" } });
        assert.equal(result.allow, false);
    });

    it("blocks drop database", () => {
        const result = commitGuard({ arguments: { command: "DROP DATABASE production" } });
        assert.equal(result.allow, false);
    });

    it("allows safe commands", () => {
        const result = commitGuard({ arguments: { command: "git status" } });
        assert.equal(result.allow, true);
    });

    it("allows npm install", () => {
        const result = commitGuard({ arguments: { command: "npm install express" } });
        assert.equal(result.allow, true);
    });
});

describe("shouldAutoLint", () => {
    it("triggers for .js files", () => {
        assert.equal(shouldAutoLint({ tool_name: "file_write", arguments: { path: "src/app.js" } }), true);
    });

    it("triggers for .ts files", () => {
        assert.equal(shouldAutoLint({ tool_name: "file_write", arguments: { path: "src/app.ts" } }), true);
    });

    it("ignores non-code files", () => {
        assert.equal(shouldAutoLint({ tool_name: "file_write", arguments: { path: "data.json" } }), false);
    });

    it("ignores non-write tools", () => {
        assert.equal(shouldAutoLint({ tool_name: "file_read", arguments: { path: "src/app.js" } }), false);
    });
});

describe("shouldAutoTest", () => {
    it("triggers for .test. files", () => {
        assert.equal(shouldAutoTest({ tool_name: "file_write", arguments: { path: "src/app.test.js" } }), true);
    });

    it("triggers for .spec. files", () => {
        assert.equal(shouldAutoTest({ tool_name: "file_write", arguments: { path: "src/app.spec.ts" } }), true);
    });

    it("ignores non-test files", () => {
        assert.equal(shouldAutoTest({ tool_name: "file_write", arguments: { path: "src/app.js" } }), false);
    });
});

describe("tokenAlert", () => {
    it("alerts above threshold", () => {
        const result = tokenAlert(150_000, 100_000);
        assert.equal(result.alert, true);
        assert.ok(result.message.includes("150,000"));
    });

    it("does not alert below threshold", () => {
        const result = tokenAlert(50_000, 100_000);
        assert.equal(result.alert, false);
    });
});

describe("HookPermissions", () => {
    it("allows by default", () => {
        const perms = new HookPermissions();
        const result = perms.check("file_read", { path: "/tmp/test" });
        assert.equal(result.allowed, true);
    });

    it("blocks by deny pattern", () => {
        const perms = new HookPermissions({
            denyPatterns: { shell_exec: ["rm.*-rf"] },
        });
        const result = perms.check("shell_exec", { command: "rm -rf /tmp" });
        assert.equal(result.allowed, false);
    });

    it("blocks shell_exec with dangerous commands via commit guard", () => {
        const perms = new HookPermissions();
        const result = perms.check("shell_exec", { command: "git push --force" });
        assert.equal(result.allowed, false);
    });
});

describe("HookChain", () => {
    it("executes hooks in order", async () => {
        const chain = new HookChain();
        const log = [];
        chain.add("first", async (p) => { log.push("first"); return { step: 1 }; });
        chain.add("second", async (p) => { log.push("second"); return { step: 2 }; });

        const { results } = await chain.execute({});
        assert.deepEqual(log, ["first", "second"]);
        assert.equal(results.length, 2);
    });

    it("stops on stop signal", async () => {
        const chain = new HookChain();
        const log = [];
        chain.add("first", async () => { log.push("first"); return { stop: true }; });
        chain.add("second", async () => { log.push("second"); });

        await chain.execute({});
        assert.deepEqual(log, ["first"]);
    });

    it("skips hooks that fail condition", async () => {
        const chain = new HookChain();
        const log = [];
        chain.add("conditional", async () => { log.push("ran"); }, {
            condition: (p) => p.shouldRun === true,
        });

        await chain.execute({ shouldRun: false });
        assert.deepEqual(log, []);

        await chain.execute({ shouldRun: true });
        assert.deepEqual(log, ["ran"]);
    });
});

describe("getBuiltinHooks", () => {
    it("returns all built-in hooks", () => {
        const hooks = getBuiltinHooks();
        assert.ok(hooks["auto-lint"]);
        assert.ok(hooks["auto-test"]);
        assert.ok(hooks["commit-guard"]);
        assert.ok(hooks["token-alert"]);
    });
});
