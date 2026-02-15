import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFile, writeFile, mkdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { Session } from "./session.js";
import { ContextManager } from "./context.js";
import { TokenCounter } from "./tokens.js";

describe("Session", () => {
  const testDir = join(process.cwd(), ".test-sessions");

  before(async () => {
    await mkdir(testDir, { recursive: true });
  });

  after(async () => {
    await rm(testDir, { recursive: true, force: true });
  });

  it("creates a session with default values", () => {
    const session = new Session();
    assert.ok(session.sessionId);
    assert.equal(session.model, "llama3.2");
    assert.equal(session.provider, "ollama");
    assert.ok(session.context instanceof ContextManager);
    assert.ok(session.tokenCounter instanceof TokenCounter);
    assert.equal(session.hooksEnabled, true);
  });

  it("creates a session with custom values", () => {
    const context = new ContextManager();
    const tokenCounter = new TokenCounter("anthropic", 200_000);
    const session = new Session({
      sessionId: "test-123",
      model: "claude-3",
      provider: "anthropic",
      context,
      tokenCounter,
      hooksEnabled: false,
    });

    assert.equal(session.sessionId, "test-123");
    assert.equal(session.model, "claude-3");
    assert.equal(session.provider, "anthropic");
    assert.equal(session.context, context);
    assert.equal(session.tokenCounter, tokenCounter);
    assert.equal(session.hooksEnabled, false);
  });

  it("starts a session", async () => {
    const session = new Session();
    await session.start();
    const systemMsg = session.context.getMessagesForApi()[0];
    assert.ok(systemMsg);
    assert.equal(systemMsg.role, "system");
    assert.ok((systemMsg.content as string).includes("You help developers"));
  });

  it("tracks message count", () => {
    const session = new Session();
    assert.equal(session.messageCount, 0);
    session["_messageCount"] = 5;
    assert.equal(session.messageCount, 5);
  });

  it("gets session status", () => {
    const session = new Session({
      sessionId: "status-test",
      model: "gpt-4",
      provider: "openai",
    });
    session["_messageCount"] = 10;
    session.tokenCounter.update({ promptTokens: 500, completionTokens: 250, totalTokens: 750 });
    session.tokenCounter.setContext(750, 128_000);

    const status = session.getStatus();
    assert.equal(status.sessionId, "status-test");
    assert.equal(status.model, "gpt-4");
    assert.equal(status.provider, "openai");
    assert.equal(status.messageCount, 10);
    assert.equal(status.tokenUsage.totalTokens, 750);
    assert.equal(status.tokenUsage.promptTokens, 500);
    assert.equal(status.tokenUsage.completionTokens, 250);
    // Context usage comes from ContextManager, which may be 0 if no messages
    assert.ok(status.contextUsage.max > 0);
  });

  it("saves and loads a session", async () => {
    const session = new Session({
      sessionId: "save-test",
      model: "llama3.2",
      provider: "ollama",
    });
    await session.start();
    session["_messageCount"] = 3;
    session.tokenCounter.update({ promptTokens: 100, completionTokens: 50, totalTokens: 150 });

    const savePath = join(testDir, "test-session.json");
    const actualPath = await session.save(savePath);

    // Verify file exists and has content
    const content = await readFile(actualPath, "utf-8");
    const data = JSON.parse(content);
    assert.equal(data.sessionId, "save-test");
    assert.equal(data.model, "llama3.2");
    assert.equal(data.provider, "ollama");
    assert.equal(data.messageCount, 3);

    // Load the session using the saved path directly
    const loaded = await Session.load("save-test", actualPath);
    assert.equal(loaded.sessionId, "save-test");
    assert.equal(loaded.model, "llama3.2");
    assert.equal(loaded.provider, "ollama");
    assert.equal(loaded.messageCount, 3);
    assert.equal(loaded.tokenCounter.promptTokens, 100);
    assert.equal(loaded.tokenCounter.completionTokens, 50);
    assert.equal(loaded.tokenCounter.totalTokens, 150);
  });

  it("generates session summary via end()", async () => {
    const session = new Session({
      sessionId: "summary-test",
      model: "gpt-4",
      provider: "openai",
    });
    session["startTime"] = new Date(Date.now() - 60_000); // 1 minute ago
    session["_messageCount"] = 5;
    session.tokenCounter.update({ promptTokens: 500, completionTokens: 250, totalTokens: 750 });

    const summary = await session.end();
    assert.equal(summary.sessionId, "summary-test");
    assert.equal(summary.model, "gpt-4");
    assert.equal(summary.provider, "openai");
    assert.equal(summary.messages, 5);
    assert.equal(summary.totalTokens, 750);
    assert.ok(typeof summary.durationSeconds === "number");
    assert.ok(summary.durationStr);
  });

  it("formats duration correctly", () => {
    assert.equal(Session.formatDuration(45), "45s");
    assert.equal(Session.formatDuration(90), "1m 30s");
    assert.equal(Session.formatDuration(3665), "1h 1m 5s");
  });

  it("ends a session", async () => {
    const session = new Session();
    await session.start();
    session["_messageCount"] = 2;

    const summary = await session.end();
    assert.ok(summary.durationSeconds >= 0);
  });
});
