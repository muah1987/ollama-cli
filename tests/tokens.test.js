/**
 * Unit tests for TokenCounter.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { TokenCounter } from "../core/tokens.js";

describe("TokenCounter", () => {
    it("initializes with zero values", () => {
        const tc = new TokenCounter("ollama");
        assert.equal(tc.totalTokens, 0);
        assert.equal(tc.promptTokens, 0);
        assert.equal(tc.completionTokens, 0);
        assert.equal(tc.costEstimate, 0);
    });

    it("updates token counts", () => {
        const tc = new TokenCounter("anthropic");
        tc.update({ promptTokens: 100, completionTokens: 50, totalTokens: 150 });
        assert.equal(tc.promptTokens, 100);
        assert.equal(tc.completionTokens, 50);
        assert.equal(tc.totalTokens, 150);
    });

    it("calculates cost for Anthropic", () => {
        const tc = new TokenCounter("anthropic");
        tc.update({ promptTokens: 1_000_000, completionTokens: 100_000, totalTokens: 1_100_000 });
        // 1M input * $3/M + 100K output * $15/M = $3 + $1.5 = $4.5
        assert.ok(tc.costEstimate > 4);
        assert.ok(tc.costEstimate < 5);
    });

    it("calculates zero cost for Ollama", () => {
        const tc = new TokenCounter("ollama");
        tc.update({ promptTokens: 1_000_000, completionTokens: 1_000_000, totalTokens: 2_000_000 });
        assert.equal(tc.costEstimate, 0);
    });

    it("computes tokens per second", () => {
        const tc = new TokenCounter("anthropic");
        tc.update({ promptTokens: 100, completionTokens: 500, totalTokens: 600 }, 1000);
        assert.equal(tc.tokensPerSecond, 500);
    });

    it("formats display string", () => {
        const tc = new TokenCounter("anthropic");
        tc.setContext(5000, 128_000);
        tc.update({ promptTokens: 5000, completionTokens: 200, totalTokens: 5200 });
        const display = tc.formatDisplay();
        assert.ok(display.includes("tok:"));
        assert.ok(display.includes("tok/s"));
        assert.ok(display.includes("$"));
    });

    it("serializes and deserializes", () => {
        const tc = new TokenCounter("anthropic", 64_000);
        tc.update({ promptTokens: 1000, completionTokens: 500, totalTokens: 1500 });
        tc.setContext(2000, 64_000);

        const json = tc.toJSON();
        const restored = TokenCounter.fromJSON(json);
        assert.equal(restored.promptTokens, 1000);
        assert.equal(restored.completionTokens, 500);
        assert.equal(restored.contextMax, 64_000);
    });

    it("resets counters", () => {
        const tc = new TokenCounter("anthropic");
        tc.update({ promptTokens: 1000, completionTokens: 500, totalTokens: 1500 });
        tc.reset();
        assert.equal(tc.totalTokens, 0);
        assert.equal(tc.costEstimate, 0);
    });
});
