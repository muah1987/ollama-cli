import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { unlink, mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { Session } from "./session.js";

describe("Session", () => {
  const testSessionDir = "/tmp/qarin-test-sessions";

  beforeEach(async () => {
    await mkdir(testSessionDir, { recursive: true });
  });

  afterEach(async () => {
    // Clean up test files
    try {
      const { readdir } = await import("node:fs/promises");
      const files = await readdir(testSessionDir);
      await Promise.all(
        files.map((file) => unlink(join(testSessionDir, file)).catch(() => {})),
      );
    } catch {
      // Ignore cleanup errors
    }
  });

  it("creates a new session with default values", () => {
    const session = new Session();
    assert.ok(session.sessionId);
    assert.equal(session.model, "llama3.2");
    assert.equal(session.provider, "ollama");
    assert.ok(session.context);
    assert.ok(session.tokenCounter);
    assert.equal(session.hooksEnabled, true);
  });

  it("creates session with custom options", () => {
    const session = new Session({
      sessionId: "test-123",
      model: "gpt-4",
      provider: "openai",
      hooksEnabled: false,
    });
    assert.equal(session.sessionId, "test-123");
    assert.equal(session.model, "gpt-4");
    assert.equal(session.provider, "openai");
    assert.equal(session.hooksEnabled, false);
  });

  it("starts session and loads QARIN.md if available", async () => {
    const qarinPath = join(testSessionDir, "QARIN.md");
    await writeFile(
      qarinPath,
      "# Project Context\nThis is a test project.\n",
      "utf-8",
    );

    // Change to test directory
    const originalCwd = process.cwd();
    process.chdir(testSessionDir);

    try {
      const session = new Session();
      await session.start();
      const status = session.getStatus();
      // System message should contain QARIN.md content
      const messages = session.context.getMessagesForApi();
      assert.ok(messages.length > 0);
      assert.ok(messages[0].content.includes("Project Context"));
    } finally {
      process.chdir(originalCwd);
    }
  });

  it("saves and loads session state", async () => {
    const session = new Session({
      sessionId: "save-test",
      model: "claude-3",
      provider: "anthropic",
    });

    // Start session to initialize
    await session.start();

    session.context.addMessage("user", "Hello, world!");
    session.context.addMessage("assistant", "Hi there!");
    session.recordMessage(); // Record the message exchange
    session.tokenCounter.update({
      promptTokens: 100,
      completionTokens: 50,
      totalTokens: 150,
    });

    const savePath = join(testSessionDir, "test-session.json");
    await session.save(savePath);

    // Load using sessionId and explicit path
    const loaded = await Session.load("save-test", savePath);
    assert.equal(loaded.sessionId, "save-test");
    assert.equal(loaded.model, "claude-3");
    assert.equal(loaded.provider, "anthropic");

    const status = loaded.getStatus();
    assert.equal(status.messageCount, 1); // One recorded message exchange
    assert.equal(status.tokenUsage.totalTokens, 150);
    assert.equal(status.tokenUsage.promptTokens, 100);
    assert.equal(status.tokenUsage.completionTokens, 50);
  });

  it("generates session status", () => {
    const session = new Session({
      sessionId: "status-test",
      model: "llama3.2",
      provider: "ollama",
    });

    session.recordMessage();
    
    // Add a message to the context so it has content
    session.context.addMessage("user", "Test message");
    
    session.tokenCounter.update({
      promptTokens: 200,
      completionTokens: 100,
      totalTokens: 300,
    });

    const status = session.getStatus();
    assert.equal(status.sessionId, "status-test");
    assert.equal(status.model, "llama3.2");
    assert.equal(status.provider, "ollama");
    assert.equal(status.messageCount, 1);
    assert.equal(status.tokenUsage.totalTokens, 300);
    assert.equal(status.tokenUsage.promptTokens, 200);
    assert.equal(status.tokenUsage.completionTokens, 100);
    // Context usage is calculated from actual message content, not tokenCounter
    assert.ok(status.contextUsage.used > 0);
    assert.ok(status.contextUsage.max > 0);
  });

  it("tracks message exchanges", () => {
    const session = new Session();
    const initialCount = session.messageCount;

    session.recordMessage();
    session.recordMessage();

    assert.equal(session.messageCount, initialCount + 2);
  });
});
