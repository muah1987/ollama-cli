/**
 * Unit tests for ContextManager.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ContextManager } from "../core/context.js";

describe("ContextManager", () => {
    it("initializes with default values", () => {
        const ctx = new ContextManager();
        assert.equal(ctx.messageCount, 0);
        assert.equal(ctx.promptTokens, 0);
        assert.equal(ctx.completionTokens, 0);
    });

    it("sets and uses system message", () => {
        const ctx = new ContextManager();
        ctx.setSystemMessage("You are a test bot.");
        const msgs = ctx.getMessagesForApi();
        assert.equal(msgs.length, 1);
        assert.equal(msgs[0].role, "system");
        assert.equal(msgs[0].content, "You are a test bot.");
    });

    it("adds messages and tracks count", () => {
        const ctx = new ContextManager();
        ctx.addMessage("user", "Hello");
        ctx.addMessage("assistant", "Hi there!");
        assert.equal(ctx.messageCount, 2);
        const msgs = ctx.getMessagesForApi();
        assert.equal(msgs.length, 2);
    });

    it("includes system message in API messages", () => {
        const ctx = new ContextManager();
        ctx.setSystemMessage("System prompt");
        ctx.addMessage("user", "Test");
        const msgs = ctx.getMessagesForApi();
        assert.equal(msgs.length, 2);
        assert.equal(msgs[0].role, "system");
        assert.equal(msgs[1].role, "user");
    });

    it("compacts when over threshold", () => {
        const ctx = new ContextManager(1000, 0.01, true, 2);
        for (let i = 0; i < 10; i++) {
            ctx.addMessage("user", `Message ${i} with some content to fill space.`);
        }
        // After compaction, should have keepLastN + 1 compacted msg
        assert.ok(ctx.messageCount <= 3);
    });

    it("creates sub-contexts", () => {
        const ctx = new ContextManager();
        const sub = ctx.createSubContext("test-sub", "Sub system prompt");
        assert.ok(sub);
        assert.equal(sub.messageCount, 0);
        sub.addMessage("user", "Sub message");
        assert.equal(sub.messageCount, 1);
        // Parent should not be affected
        assert.equal(ctx.messageCount, 0);
    });

    it("tracks context usage", () => {
        const ctx = new ContextManager(128_000);
        ctx.addMessage("user", "A".repeat(400)); // ~100 tokens
        const usage = ctx.getContextUsage();
        assert.ok(usage.used > 0);
        assert.equal(usage.max, 128_000);
        assert.ok(usage.percent >= 0);
    });

    it("serializes and deserializes", () => {
        const ctx = new ContextManager(64_000);
        ctx.setSystemMessage("Sys");
        ctx.addMessage("user", "Hello");
        ctx.addMessage("assistant", "World");
        ctx.updateMetrics(100, 50);

        const json = ctx.toJSON();
        const restored = ContextManager.fromJSON(json);
        assert.equal(restored.messageCount, 2);
        assert.equal(restored.promptTokens, 100);
        assert.equal(restored.completionTokens, 50);
    });

    it("getRecentMessages returns last N", () => {
        const ctx = new ContextManager();
        for (let i = 0; i < 10; i++) {
            ctx.addMessage("user", `Msg ${i}`);
        }
        const recent = ctx.getRecentMessages(3);
        assert.equal(recent.length, 3);
        assert.equal(recent[0].content, "Msg 7");
    });
});
