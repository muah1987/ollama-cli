import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { IntentClassifier, classifyIntent } from "./intent.js";

describe("IntentClassifier", () => {
  const classifier = new IntentClassifier();

  it("classifies code intents", () => {
    const result = classifier.classify("Write a function to parse JSON");
    assert.equal(result.agentType, "code");
    assert.ok(result.confidence > 0);
    assert.ok(result.matchedPatterns.length > 0);
  });

  it("classifies debug intents", () => {
    const result = classifier.classify("Debug the crash in payment handler");
    assert.equal(result.agentType, "debug");
    assert.ok(result.confidence >= 0.7);
  });

  it("classifies test intents", () => {
    // Use a prompt where test keywords dominate (avoid "write" which gives code a 2x bonus)
    const result = classifier.classify("Add unit test coverage for the auth module test suite");
    assert.equal(result.agentType, "test");
  });

  it("classifies review intents", () => {
    const result = classifier.classify("Review the pull request for security issues");
    assert.equal(result.agentType, "review");
  });

  it("classifies plan intents", () => {
    // Use a prompt where plan keywords dominate
    const result = classifier.classify("Plan the design and architecture approach for the specification");
    assert.equal(result.agentType, "plan");
  });

  it("classifies docs intents", () => {
    // Use a prompt where docs keywords dominate
    const result = classifier.classify("Document and annotate the usage of the help text");
    assert.equal(result.agentType, "docs");
  });

  it("classifies research intents", () => {
    const result = classifier.classify("Research the best practices for error handling");
    assert.equal(result.agentType, "research");
  });

  it("classifies team intents", () => {
    const result = classifier.classify("Complete this with team build");
    assert.equal(result.agentType, "team");
  });

  it("returns low confidence for ambiguous prompts", () => {
    const result = classifier.classify("Hello, how are you?");
    assert.ok(result.confidence < 0.7);
  });

  it("handles empty prompts", () => {
    const result = classifier.classify("");
    assert.equal(result.confidence, 0);
  });

  it("applies early-position bonus", () => {
    // "Write" at start should score higher
    const r1 = classifier.classify("Write a function to parse JSON");
    const r2 = classifier.classify("I want you to parse JSON and write something");
    // Both should classify as code, but r1 should have higher confidence
    assert.equal(r1.agentType, "code");
    assert.equal(r2.agentType, "code");
    assert.ok(r1.confidence >= r2.confidence);
  });

  it("convenience function works", () => {
    const result = classifyIntent("Fix the broken test", 0.5);
    assert.ok(result.agentType !== undefined);
    assert.ok(result.confidence > 0);
  });

  it("provides explanation in result", () => {
    const result = classifier.classify("Implement the login feature");
    assert.ok(result.explanation);
    assert.ok(result.explanation.length > 0);
  });
});
