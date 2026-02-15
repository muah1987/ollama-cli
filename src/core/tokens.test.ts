import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { TokenCounter } from "./tokens.js";

describe("TokenCounter", () => {
  it("initializes with zero values", () => {
    const tc = new TokenCounter("ollama", 4096);
    assert.equal(tc.totalTokens, 0);
    assert.equal(tc.promptTokens, 0);
    assert.equal(tc.completionTokens, 0);
    assert.equal(tc.tokensPerSecond, 0);
    assert.equal(tc.costEstimate, 0);
    assert.equal(tc.provider, "ollama");
    assert.equal(tc.contextMax, 4096);
  });

  it("updates token counts", () => {
    const tc = new TokenCounter("ollama", 4096);
    tc.update({ promptTokens: 100, completionTokens: 200, totalTokens: 300 });
    assert.equal(tc.promptTokens, 100);
    assert.equal(tc.completionTokens, 200);
    assert.equal(tc.totalTokens, 300);
  });

  it("accumulates over multiple updates", () => {
    const tc = new TokenCounter("ollama", 4096);
    tc.update({ promptTokens: 50, completionTokens: 100, totalTokens: 150 });
    tc.update({ promptTokens: 50, completionTokens: 100, totalTokens: 150 });
    assert.equal(tc.promptTokens, 100);
    assert.equal(tc.completionTokens, 200);
    assert.equal(tc.totalTokens, 300);
  });

  it("calculates tokens per second", () => {
    const tc = new TokenCounter("ollama", 4096);
    tc.update(
      { promptTokens: 100, completionTokens: 200, totalTokens: 300 },
      2000, // 2 seconds
    );
    assert.equal(tc.tokensPerSecond, 100); // 200 tokens / 2 seconds
  });

  it("estimates zero cost for ollama", () => {
    const tc = new TokenCounter("ollama", 4096);
    tc.update({ promptTokens: 1000, completionTokens: 500, totalTokens: 1500 });
    assert.equal(tc.costEstimate, 0);
  });

  it("estimates cost for anthropic", () => {
    const tc = new TokenCounter("anthropic", 200_000);
    tc.update({ promptTokens: 1_000_000, completionTokens: 100_000, totalTokens: 1_100_000 });
    // Input: 1M * $3/M = $3.00, Output: 100K * $15/M = $1.50
    assert.ok(tc.costEstimate > 4);
    assert.ok(tc.costEstimate < 5);
  });

  it("estimates cost for openai", () => {
    const tc = new TokenCounter("openai", 128_000);
    tc.update({ promptTokens: 1_000_000, completionTokens: 1_000_000, totalTokens: 2_000_000 });
    // Input: 1M * $1/M = $1.00, Output: 1M * $2/M = $2.00
    assert.equal(tc.costEstimate, 3);
  });

  it("formats display string", () => {
    const tc = new TokenCounter("ollama", 4096);
    tc.update({ promptTokens: 100, completionTokens: 200, totalTokens: 300 }, 1000);
    const display = tc.formatDisplay();
    assert.ok(display.includes("tok:"));
    assert.ok(display.includes("tok/s"));
    assert.ok(display.includes("$"));
  });

  it("serializes to JSON", () => {
    const tc = new TokenCounter("anthropic", 128_000);
    tc.update({ promptTokens: 500, completionTokens: 250, totalTokens: 750 });
    const json = tc.toJSON();
    assert.equal(json.promptTokens, 500);
    assert.equal(json.completionTokens, 250);
    assert.equal(json.totalTokens, 750);
    assert.equal(json.provider, "anthropic");
  });

  it("resets counters", () => {
    const tc = new TokenCounter("ollama", 4096);
    tc.update({ promptTokens: 100, completionTokens: 200, totalTokens: 300 });
    tc.reset();
    assert.equal(tc.totalTokens, 0);
    assert.equal(tc.promptTokens, 0);
    assert.equal(tc.completionTokens, 0);
    assert.equal(tc.costEstimate, 0);
  });

  it("sets context window", () => {
    const tc = new TokenCounter("ollama", 4096);
    tc.setContext(2048, 8192);
    assert.equal(tc.contextUsed, 2048);
    assert.equal(tc.contextMax, 8192);
  });

  it("restores state from JSON", () => {
    const tc = new TokenCounter("anthropic", 128_000);
    tc.update({ promptTokens: 500, completionTokens: 250, totalTokens: 750 }, 1000);
    tc.setContext(1000, 128_000);

    const json = tc.toJSON();
    const restored = TokenCounter.fromJSON(json);

    assert.equal(restored.promptTokens, 500);
    assert.equal(restored.completionTokens, 250);
    assert.equal(restored.totalTokens, 750);
    assert.equal(restored.contextUsed, 1000);
    assert.equal(restored.contextMax, 128_000);
    assert.equal(restored.provider, "anthropic");
    // Cost should be recalculated
    assert.ok(restored.costEstimate > 0);
  });

  it("handles invalid JSON values gracefully", () => {
    const restored = TokenCounter.fromJSON({
      promptTokens: NaN,
      completionTokens: Infinity,
      tokensPerSecond: NaN, // Should be set to 0, not kept as NaN
      contextUsed: 0,
      contextMax: 4096,
      provider: "ollama",
    });

    assert.equal(restored.promptTokens, 0);
    assert.equal(restored.completionTokens, 0);
    assert.equal(restored.tokensPerSecond, 0);
  });
});
