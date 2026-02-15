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
/** Maps agent type -> list of keyword / multi-word patterns */
const PATTERN_REGISTRY = {
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
/**
 * Pattern-based intent classifier (Tier 1).
 *
 * Scores each agent type by counting pattern matches in the user prompt,
 * applying a 2x weight for matches in the first five words.
 */
export class IntentClassifier {
    threshold;
    compiled;
    constructor(confidenceThreshold = 0.7) {
        this.threshold = confidenceThreshold;
        this.compiled = new Map();
        for (const [agentType, patterns] of Object.entries(PATTERN_REGISTRY)) {
            const compiledPatterns = patterns.map((pattern) => {
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
    classify(prompt) {
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
        const scores = new Map();
        const matches = new Map();
        const firstMatchPositions = new Map();
        for (const [agentType, compiledPatterns] of this.compiled) {
            let typeScore = 0;
            const typeMatches = [];
            let earliestPos = null;
            for (const { text, matcher } of compiledPatterns) {
                let matched = false;
                let matchPos = null;
                if (matcher instanceof RegExp) {
                    const m = matcher.exec(promptLower);
                    if (m) {
                        matched = true;
                        matchPos = m.index;
                    }
                }
                else {
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
                    }
                    else if (firstFive.includes(matcher)) {
                        weight = 2.0;
                    }
                    typeScore += weight;
                    if (matchPos !== null &&
                        (earliestPos === null || matchPos < earliestPos)) {
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
        let bestType = null;
        let bestScore = 0;
        for (const [agentType, score] of scores) {
            if (score > bestScore) {
                bestScore = score;
                bestType = agentType;
            }
            else if (score === bestScore && score > 0) {
                // Tie-breaking: prefer the type whose first match appears earliest
                const currentPos = firstMatchPositions.get(agentType) ?? prompt.length;
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
            agentType: (bestType ?? "code"),
            confidence,
            matchedPatterns,
            explanation: `Classified as '${bestType}' with confidence ${confidence.toFixed(2)} based on ${matchedPatterns.length} pattern match(es): ${matchedPatterns.join(", ")}.`,
        };
    }
}
    /**
     * Tier 2: LLM-based classification fallback.
     *
     * When Tier 1 confidence is below threshold, ask the active model
     * to classify intent via structured prompt. Also supports
     * context-aware classification by factoring in recent messages.
     *
     * @param prompt - User prompt to classify
     * @param orchestrator - ModelOrchestrator for LLM calls
     * @param provider - Provider to use for LLM call
     * @param recentMessages - Last N messages for context-aware classification
     * @returns ClassificationResult with LLM-derived intent
     */
    async classifyWithLLM(prompt, orchestrator, provider, recentMessages = []) {
        const tier1Result = this.classify(prompt);
        // If Tier 1 is confident enough, return it
        if (tier1Result.confidence >= this.threshold) {
            return tier1Result;
        }
        // Build context from recent messages for context-aware classification
        const contextBlock = recentMessages.length > 0
            ? `\nRecent conversation context:\n${recentMessages.map((m) => `[${m.role}]: ${m.content.slice(0, 200)}`).join("\n")}\n`
            : "";
        const classifyPrompt = [
            "Classify the following user message into exactly one agent type.",
            "Available types: code, review, test, debug, plan, docs, orchestrator, research, team",
            "",
            "Rules:",
            "- Consider the conversation context if provided",
            '- A short follow-up like "do it" or "yes" after a plan -> code',
            '- "looks good" after code -> review',
            "- Return ONLY a JSON object with these fields:",
            '  { "agentType": string, "confidence": number 0-1, "explanation": string }',
            contextBlock,
            `User message: ${prompt}`,
        ].join("\n");
        try {
            const response = await orchestrator.complete(provider, [
                { role: "system", content: "You are an intent classifier. Return only valid JSON." },
                { role: "user", content: classifyPrompt },
            ]);
            // Parse the LLM response
            let parsed = null;
            try {
                parsed = JSON.parse(response.content);
            }
            catch {
                const match = response.content.match(/\{[\s\S]*\}/);
                if (match) {
                    try {
                        parsed = JSON.parse(match[0]);
                    }
                    catch { }
                }
            }
            if (parsed?.agentType) {
                const validTypes = Object.keys(PATTERN_REGISTRY);
                const agentType = validTypes.includes(parsed.agentType) ? parsed.agentType : "code";
                return {
                    agentType,
                    confidence: typeof parsed.confidence === "number" ? parsed.confidence : 0.8,
                    matchedPatterns: tier1Result.matchedPatterns,
                    explanation: parsed.explanation ?? `LLM classified as '${agentType}'`,
                    tier: 2,
                };
            }
        }
        catch {
            // LLM call failed, return Tier 1 result
        }
        return {
            ...tier1Result,
            explanation: `Tier 2 LLM fallback failed. ${tier1Result.explanation}`,
        };
    }
}
/**
 * Convenience function: classify a user prompt into an agent type.
 */
export function classifyIntent(prompt, threshold = 0.7) {
    const classifier = new IntentClassifier(threshold);
    return classifier.classify(prompt);
}
//# sourceMappingURL=intent.js.map