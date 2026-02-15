/**
 * Intent classifier -- Two-tier classification strategy.
 *
 * Ports the Python runner/intent_classifier.py into TypeScript.
 *
 * Tier 1: Fast, deterministic pattern matching with keyword and
 * multi-word patterns. Each agent type is scored by counting pattern
 * hits, with an early-position bonus for matches in the first five words.
 *
 * Tier 2: LLM fallback (external) when Tier 1 confidence is below threshold.
 */

import type { AgentType, IntentResult } from "../types/agent.js";

/** Maps agent type -> list of keyword / multi-word patterns */
const PATTERN_REGISTRY: Record<string, string[]> = {
  code: [
    "write",
    "implement",
    "create function",
    "add feature",
    "build",
    "code",
    "fix bug",
    "refactor",
    "add endpoint",
    "create class",
    "generate",
    "scaffold",
    "function",
    "method",
    "class",
    "module",
    "api",
    "endpoint",
    "component",
  ],
  review: [
    "review",
    "check",
    "audit",
    "inspect",
    "analyze code",
    "look at",
    "examine",
    "evaluate quality",
    "code review",
    "pull request",
    "pr review",
  ],
  test: [
    "test",
    "write tests",
    "add tests",
    "unit test",
    "integration test",
    "coverage",
    "assert",
    "verify behavior",
    "pytest",
    "test case",
    "test suite",
  ],
  debug: [
    "debug",
    "fix error",
    "traceback",
    "exception",
    "crash",
    "not working",
    "broken",
    "investigate",
    "troubleshoot",
    "stack trace",
    "segfault",
    "error message",
    "why does",
    "fails",
  ],
  plan: [
    "plan",
    "design",
    "architect",
    "strategy",
    "roadmap",
    "spec",
    "specification",
    "approach",
    "how should",
    "what's the best way",
    "implementation plan",
    "design pattern",
  ],
  docs: [
    "document",
    "docstring",
    "readme",
    "explain",
    "describe",
    "comment",
    "annotate",
    "documentation",
    "api docs",
    "help text",
    "usage",
  ],
  orchestrator: [
    "orchestrate",
    "coordinate",
    "multi-step",
    "pipeline",
    "chain",
    "workflow",
    "deploy",
    "ship",
    "release",
    "ci/cd",
    "automate",
    "batch",
  ],
  research: [
    "research",
    "compare",
    "summarize",
    "what is",
    "how does",
    "explain how",
    "pros and cons",
    "alternatives",
    "benchmark",
    "evaluate options",
    "best practices",
    "state of the art",
  ],
  team: [
    "team",
    "team build",
    "complete with team",
  ],
};

/** Compiled pattern: either a RegExp (single word) or a lowercase string (multi-word) */
type CompiledPattern = { text: string; matcher: RegExp | string };

/**
 * Pattern-based intent classifier (Tier 1).
 *
 * Scores each agent type by counting pattern matches in the user prompt,
 * applying a 2x weight for matches in the first five words.
 */
export class IntentClassifier {
  private readonly threshold: number;
  private readonly compiled: Map<string, CompiledPattern[]>;

  constructor(confidenceThreshold = 0.7) {
    this.threshold = confidenceThreshold;
    this.compiled = new Map();

    for (const [agentType, patterns] of Object.entries(PATTERN_REGISTRY)) {
      const compiledPatterns: CompiledPattern[] = patterns.map((pattern) => {
        if (pattern.includes(" ") || pattern.includes("/")) {
          // Multi-word or special-char pattern -> substring match
          return { text: pattern, matcher: pattern.toLowerCase() };
        }
        // Single word -> word-boundary regex
        const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        return { text: pattern, matcher: new RegExp(`\\b${escaped}\\b`, "i") };
      });
      this.compiled.set(agentType, compiledPatterns);
    }
  }

  /**
   * Classify a user prompt into an agent type.
   */
  classify(prompt: string): IntentResult {
    if (!prompt || !prompt.trim()) {
      return {
        agentType: "code",
        confidence: 0,
        matchedPatterns: [],
        explanation: "Empty prompt cannot be classified.",
      };
    }

    const promptLower = prompt.toLowerCase();
    const words = promptLower.match(/[a-z0-9'/]+/g) ?? [];
    const firstFive = words.slice(0, 5).join(" ");

    // Score each agent type
    const scores = new Map<string, number>();
    const matches = new Map<string, string[]>();
    const firstMatchPositions = new Map<string, number>();

    for (const [agentType, compiledPatterns] of this.compiled) {
      let typeScore = 0;
      const typeMatches: string[] = [];
      let earliestPos: number | null = null;

      for (const { text, matcher } of compiledPatterns) {
        let matched = false;
        let matchPos: number | null = null;

        if (matcher instanceof RegExp) {
          const m = matcher.exec(promptLower);
          if (m) {
            matched = true;
            matchPos = m.index;
          }
        } else {
          const idx = promptLower.indexOf(matcher);
          if (idx !== -1) {
            matched = true;
            matchPos = idx;
          }
        }

        if (matched) {
          typeMatches.push(text);
          let weight = 1.0;

          // Early-position bonus: 2x if pattern appears in first 5 words
          if (matcher instanceof RegExp) {
            if (matcher.test(firstFive)) {
              weight = 2.0;
            }
          } else if (firstFive.includes(matcher)) {
            weight = 2.0;
          }

          typeScore += weight;

          if (
            matchPos !== null &&
            (earliestPos === null || matchPos < earliestPos)
          ) {
            earliestPos = matchPos;
          }
        }
      }

      scores.set(agentType, typeScore);
      matches.set(agentType, typeMatches);
      if (earliestPos !== null) {
        firstMatchPositions.set(agentType, earliestPos);
      }
    }

    // Find the best agent type
    let bestType: string | null = null;
    let bestScore = 0;

    for (const [agentType, score] of scores) {
      if (score > bestScore) {
        bestScore = score;
        bestType = agentType;
      } else if (score === bestScore && score > 0) {
        // Tie-breaking: prefer the type whose first match appears earliest
        const currentPos =
          firstMatchPositions.get(agentType) ?? prompt.length;
        const bestPos = bestType
          ? (firstMatchPositions.get(bestType) ?? prompt.length)
          : prompt.length;
        if (currentPos < bestPos) {
          bestType = agentType;
        }
      }
    }

    // Normalize confidence: 3+ raw score maps to 1.0
    const confidence = bestScore > 0 ? Math.min(1.0, bestScore / 3.0) : 0;

    // Apply threshold
    if (confidence < this.threshold) {
      return {
        agentType: "code",
        confidence,
        matchedPatterns: bestType ? (matches.get(bestType) ?? []) : [],
        explanation: `No agent type met the confidence threshold of ${this.threshold.toFixed(1)}. Best candidate was '${bestType}' with confidence ${confidence.toFixed(2)}.`,
      };
    }

    const matchedPatterns = bestType ? (matches.get(bestType) ?? []) : [];

    return {
      agentType: (bestType ?? "code") as AgentType,
      confidence,
      matchedPatterns,
      explanation: `Classified as '${bestType}' with confidence ${confidence.toFixed(2)} based on ${matchedPatterns.length} pattern match(es): ${matchedPatterns.join(", ")}.`,
    };
  }
}

/**
 * Convenience function: classify a user prompt into an agent type.
 */
export function classifyIntent(
  prompt: string,
  threshold = 0.7,
): IntentResult {
  const classifier = new IntentClassifier(threshold);
  return classifier.classify(prompt);
}
