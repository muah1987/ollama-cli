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
import type { IntentResult } from "../types/agent.js";
/**
 * Pattern-based intent classifier (Tier 1).
 *
 * Scores each agent type by counting pattern matches in the user prompt,
 * applying a 2x weight for matches in the first five words.
 */
export declare class IntentClassifier {
    private readonly threshold;
    private readonly compiled;
    constructor(confidenceThreshold?: number);
    /**
     * Classify a user prompt into an agent type.
     */
    classify(prompt: string): IntentResult;
}
/**
 * Convenience function: classify a user prompt into an agent type.
 */
export declare function classifyIntent(prompt: string, threshold?: number): IntentResult;
//# sourceMappingURL=intent.d.ts.map