/**
 * Unit tests for IntentClassifier.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { IntentClassifier, classifyIntent } from "../core/intent.js";

describe("IntentClassifier", () => {
    it("classifies code-related prompts", () => {
        const c = new IntentClassifier();
        const result = c.classify("Write a function to sort an array");
        assert.equal(result.agentType, "code");
        assert.ok(result.confidence > 0.5);
    });

    it("classifies debug prompts", () => {
        const c = new IntentClassifier(0.5);
        const result = c.classify("Debug this error: TypeError: undefined is not a function");
        assert.equal(result.agentType, "debug");
        assert.ok(result.confidence > 0);
    });

    it("classifies test prompts", () => {
        const c = new IntentClassifier(0.5);
        const result = c.classify("Add tests for the test suite to improve coverage");
        assert.equal(result.agentType, "test");
        assert.ok(result.confidence > 0.5);
    });

    it("classifies plan prompts", () => {
        const c = new IntentClassifier(0.5);
        const result = c.classify("Design the architecture for a REST API");
        assert.equal(result.agentType, "plan");
        assert.ok(result.confidence > 0.5);
    });

    it("classifies docs prompts", () => {
        const c = new IntentClassifier();
        const result = c.classify("Document the API endpoints in the readme");
        assert.equal(result.agentType, "docs");
        assert.ok(result.confidence > 0.5);
    });

    it("classifies review prompts", () => {
        const c = new IntentClassifier(0.5);
        const result = c.classify("Review this code for security issues");
        assert.equal(result.agentType, "review");
        assert.ok(result.confidence > 0.5);
    });

    it("returns low confidence for empty input", () => {
        const c = new IntentClassifier();
        const result = c.classify("");
        assert.equal(result.confidence, 0);
    });

    it("applies early position bonus", () => {
        const c = new IntentClassifier();
        const r1 = c.classify("write a function to test something");
        const r2 = c.classify("I want something to write some code");
        // "write" in first position should give higher score to code
        assert.ok(r1.confidence >= r2.confidence);
    });

    it("convenience function works", () => {
        const result = classifyIntent("fix the broken authentication");
        assert.ok(result.agentType);
        assert.ok(typeof result.confidence === "number");
    });

    it("returns matched patterns", () => {
        const c = new IntentClassifier();
        const result = c.classify("write a function and implement the API endpoint");
        assert.ok(result.matchedPatterns.length > 0);
    });
});
