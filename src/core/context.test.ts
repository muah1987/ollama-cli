import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ContextManager } from "./context.js";

describe("ContextManager", () => {
  it("initializes with empty messages", () => {
    const ctx = new ContextManager();
    assert.equal(ctx.messageCount, 0);
    assert.equal(ctx.promptTokens, 0);
    assert.equal(ctx.completionTokens, 0);
  });

  it("sets system message", () => {
    const ctx = new ContextManager();
    ctx.setSystemMessage("You are a helpful assistant.");
    const msgs = ctx.getMessagesForApi();
    assert.equal(msgs[0].role, "system");
    assert.equal(msgs[0].content, "You are a helpful assistant.");
  });

  it("adds user and assistant messages", () => {
    const ctx = new ContextManager();
    ctx.addMessage("user", "Hello");
    ctx.addMessage("assistant", "Hi there!");
    assert.equal(ctx.messageCount, 2);
  });

  it("returns messages with system message first", () => {
    const ctx = new ContextManager();
    ctx.setSystemMessage("system prompt");
    ctx.addMessage("user", "test");
    const msgs = ctx.getMessagesForApi();
    assert.equal(msgs.length, 2);
    assert.equal(msgs[0].role, "system");
    assert.equal(msgs[1].role, "user");
  });

  it("reports context usage", () => {
    const ctx = new ContextManager(1000);
    ctx.addMessage("user", "a".repeat(400)); // ~100 tokens
    const usage = ctx.getContextUsage();
    assert.ok(usage.used > 0);
    assert.equal(usage.max, 1000);
    assert.ok(usage.percent >= 0 && usage.percent <= 100);
  });

  it("compacts when threshold exceeded", () => {
    // Small context window to trigger compaction
    const ctx = new ContextManager(100, 0.5, true, 2);
    for (let i = 0; i < 20; i++) {
      ctx.addMessage("user", `Message ${i} with some content to fill tokens`);
      ctx.addMessage("assistant", `Response ${i} with some content to fill tokens`);
    }
    // After auto-compaction, should have fewer messages
    assert.ok(ctx.messageCount < 40);
  });

  it("manual compact keeps last N messages", () => {
    const ctx = new ContextManager(128_000, 0.85, false, 4);
    for (let i = 0; i < 10; i++) {
      ctx.addMessage("user", `msg ${i}`);
    }
    ctx.compact();
    // Should have compacted message + last 4
    assert.equal(ctx.messageCount, 5);
  });

  it("tracks token metrics", () => {
    const ctx = new ContextManager();
    ctx.updateMetrics(100, 50);
    ctx.updateMetrics(200, 100);
    assert.equal(ctx.promptTokens, 300);
    assert.equal(ctx.completionTokens, 150);
  });

  it("creates sub-contexts", () => {
    const ctx = new ContextManager();
    const sub = ctx.createSubContext("diagnostic", "You are a diagnostic agent.");
    assert.ok(sub instanceof ContextManager);
    const retrieved = ctx.getSubContext("diagnostic");
    assert.ok(retrieved !== undefined);
  });

  it("serializes and deserializes", () => {
    const ctx = new ContextManager(64_000);
    ctx.setSystemMessage("test system");
    ctx.addMessage("user", "hello");
    ctx.addMessage("assistant", "world");
    ctx.updateMetrics(50, 25);

    const json = ctx.toJSON();
    const restored = ContextManager.fromJSON(json as Record<string, unknown>);

    assert.equal(restored.messageCount, 2);
    assert.equal(restored.promptTokens, 50);
    assert.equal(restored.completionTokens, 25);
  });

  it("supports tool call messages", () => {
    const ctx = new ContextManager();
    ctx.addMessage("assistant", "Let me read that file.", {
      toolCalls: [{
        id: "call_1",
        type: "function",
        function: { name: "file_read", arguments: '{"path":"test.txt"}' },
      }],
    });
    ctx.addMessage("tool", '{"success":true,"output":"file contents"}', {
      toolCallId: "call_1",
    });
    assert.equal(ctx.messageCount, 2);
    const msgs = ctx.getMessagesForApi();
    assert.ok(msgs[0].tool_calls !== undefined);
    assert.equal(msgs[1].tool_call_id, "call_1");
  });
});
