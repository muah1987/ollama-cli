/**
 * Chain Controller -- Primary Orchestrator.
 *
 * Replaces the old sequential 4-wave SubagentOrchestrator with a
 * parallel fan-out architecture. Each wave spawns multiple sub-agents
 * concurrently, merges their outputs into a SharedState, and passes
 * that state to the next wave.
 *
 * Waves:
 *   0  Ingest      -- restate, extract constraints, init SharedState
 *   1  Analysis    -- Analyzer-A + Analyzer-B (parallel)
 *   2  Plan/Val/Opt-- Planner + Validator + Optimizer (parallel)
 *   3  Execution   -- Executor-1 + Executor-2 (parallel)
 *   4  Finalize    -- Monitor + Reporter + Cleaner (parallel)
 */
import { EventEmitter } from "node:events";
import { createHash } from "node:crypto";
import { OperationPhase } from "../types/theme.js";
import { CONTRACT_REGISTRY, ROLE_PROMPTS, DEFAULT_WAVES, createEmptySharedState, } from "../types/chain.js";
/**
 * Hash a string for dedup comparisons.
 */
function contentHash(text) {
    return createHash("sha256").update(text.trim().toLowerCase()).digest("hex").slice(0, 16);
}
/**
 * Deduplicate an array of strings by content hash.
 */
function dedup(items) {
    const seen = new Set();
    const result = [];
    for (const item of items) {
        const hash = contentHash(item);
        if (!seen.has(hash)) {
            seen.add(hash);
            result.push(item);
        }
    }
    return result;
}
/**
 * Attempt to parse a JSON object from a model response.
 *
 * Handles responses that include markdown code fences or leading text.
 */
function parseAgentResponse(text) {
    // Try raw JSON first
    try {
        return JSON.parse(text);
    }
    catch { }
    // Try extracting from markdown code fence
    const fenceMatch = text.match(/```(?:json)?\s*\n?([\s\S]*?)```/);
    if (fenceMatch) {
        try {
            return JSON.parse(fenceMatch[1].trim());
        }
        catch { }
    }
    // Try finding the first { ... } block
    const braceStart = text.indexOf("{");
    const braceEnd = text.lastIndexOf("}");
    if (braceStart !== -1 && braceEnd > braceStart) {
        try {
            return JSON.parse(text.slice(braceStart, braceEnd + 1));
        }
        catch { }
    }
    return null;
}
/**
 * ChainController -- runs sub-agent waves with parallel fan-out and
 * deterministic merging via SharedState.
 */
export class ChainController extends EventEmitter {
    orchestrator;
    context;
    provider;
    waves;
    agentConfigs;
    state;
    auditTrail = [];
    runId;
    // Adaptive execution
    intentType;
    // Token budget
    tokenBudget;
    tokenBudgetDistribution;
    tokensUsed = 0;
    // Result cache
    cache;
    constructor(options) {
        super();
        this.orchestrator = options.orchestrator;
        this.context = options.context;
        this.provider = options.provider;
        this.waves = options.waves ?? DEFAULT_WAVES;
        this.agentConfigs = options.agentConfigs ?? {};
        this.state = createEmptySharedState();
        this.runId = crypto.randomUUID().slice(0, 12);
        this.intentType = options.intentType ?? null;
        this.tokenBudget = options.tokenBudget ?? null;
        this.tokenBudgetDistribution = options.tokenBudgetDistribution ?? {
            analysis: 0.10,
            plan_validate_optimize: 0.20,
            execution: 0.50,
            finalize: 0.20,
        };
        this.cache = options.cache ?? null;
    }
    /**
     * Run the full chain: Wave 0 (ingest) then Waves 1-4.
     *
     * Supports adaptive wave selection, token budgets, early
     * termination, and result caching.
     */
    async run(userInput) {
        const startTime = Date.now();
        this.emit("chain:start", { runId: this.runId, userInput });
        try {
            // Wave 0: Ingest
            await this.ingest(userInput);
            // Determine which waves to run (adaptive execution)
            const activeWaves = this.selectWaves();
            // Waves 1-4: Fan-out and merge
            for (let i = 0; i < activeWaves.length; i++) {
                const wave = activeWaves[i];
                const waveNum = i + 1;
                // Token budget check
                if (this.tokenBudget && this.tokensUsed > this.tokenBudget) {
                    this.emit("progress", {
                        phase: OperationPhase.ERROR,
                        details: `Token budget exceeded (${this.tokensUsed}/${this.tokenBudget})`,
                    });
                    break;
                }
                // Check cache
                const cacheKey = this.buildCacheKey(wave.name);
                if (this.cache) {
                    const cached = this.cache.get(cacheKey);
                    if (cached) {
                        this.emit("wave:cached", { wave: waveNum, name: wave.name });
                        // Restore cached merge result
                        this.merge(wave.name, cached.results);
                        this.auditTrail.push(cached.audit);
                        continue;
                    }
                }
                this.emit("wave:start", {
                    wave: waveNum,
                    name: wave.name,
                    agents: wave.agents,
                });
                this.emit("progress", {
                    phase: this.waveToPhase(waveNum),
                    details: `Wave ${waveNum}: ${wave.name} (${wave.agents.join(", ")})`,
                });
                // Run all agents in this wave concurrently
                const results = await this.runWave(wave, waveNum);
                // Track token usage from results
                for (const r of results) {
                    if (r.usage) {
                        this.tokensUsed += (r.usage.promptTokens ?? 0) + (r.usage.completionTokens ?? 0);
                    }
                }
                // Merge results into SharedState
                const mergeAudit = this.merge(wave.name, results);
                this.auditTrail.push(mergeAudit);
                // Cache results
                if (this.cache) {
                    this.cache.set(cacheKey, { results, audit: mergeAudit });
                }
                this.emit("merge:complete", {
                    wave: waveNum,
                    name: wave.name,
                    audit: mergeAudit,
                });
                this.emit("wave:complete", {
                    wave: waveNum,
                    name: wave.name,
                    state: { ...this.state },
                });
                // Early termination: if Monitor passes on first check
                if (wave.name === "finalize") {
                    const monitor = this.state.wave_outputs?.monitor;
                    if (monitor?.verdict === "pass") {
                        this.emit("progress", {
                            phase: OperationPhase.COMPLETE,
                            details: "Early termination: Monitor verified success",
                        });
                    }
                }
                // Confidence gating: if Validator readiness > 90, skip to execution
                if (wave.name === "plan_validate_optimize") {
                    const readiness = this.state.wave_outputs?.readiness_score;
                    if (readiness != null && readiness > 90) {
                        this.emit("progress", {
                            phase: OperationPhase.IMPLEMENTING,
                            details: `High readiness (${readiness}), proceeding to execution`,
                        });
                    }
                }
            }
            const duration = Date.now() - startTime;
            // Build final answer from Reporter output or fallback
            const finalAnswer = this.buildFinalAnswer();
            this.emit("progress", {
                phase: OperationPhase.COMPLETE,
                details: `Chain complete (${(duration / 1000).toFixed(1)}s)`,
            });
            this.emit("chain:complete", {
                runId: this.runId,
                state: this.state,
                finalAnswer,
                duration,
                auditTrail: this.auditTrail,
            });
            return {
                finalAnswer,
                state: this.state,
                auditTrail: this.auditTrail,
                duration,
                runId: this.runId,
            };
        }
        catch (err) {
            this.emit("progress", {
                phase: OperationPhase.ERROR,
                details: `Chain failed: ${err instanceof Error ? err.message : String(err)}`,
            });
            this.emit("chain:error", {
                runId: this.runId,
                error: err instanceof Error ? err : new Error(String(err)),
            });
            throw err;
        }
    }
    /**
     * Wave 0: Ingest -- restate the request, extract constraints, init SharedState.
     */
    async ingest(userInput) {
        this.emit("progress", {
            phase: OperationPhase.ANALYZING,
            details: "Wave 0: Ingesting request...",
        });
        const ingestPrompt = [
            "You are the Primary Orchestrator. Restate the user request and extract structured information.",
            "Return a JSON object with these keys:",
            '- problem_statement: string (restate the request in 1-2 lines)',
            '- success_criteria: array of strings (how to know we are done)',
            '- constraints: array of strings (explicit + inferred)',
            '- assumptions: array of strings',
            '- artifacts_to_update: array of strings (files, configs, schemas to produce)',
        ].join("\n");
        const subCtx = this.context.createSubContext("ingest", ingestPrompt);
        subCtx.addMessage("user", userInput);
        const response = await this.orchestrator.complete(this.provider, subCtx.getMessagesForApi());
        const parsed = parseAgentResponse(response.content);
        if (parsed) {
            this.state.problem_statement = parsed.problem_statement ?? userInput;
            this.state.success_criteria = parsed.success_criteria ?? [];
            this.state.constraints = parsed.constraints ?? [];
            this.state.assumptions = parsed.assumptions ?? [];
            this.state.artifacts_to_update = parsed.artifacts_to_update ?? [];
        }
        else {
            // Fallback: use raw input
            this.state.problem_statement = userInput;
        }
        this.emit("wave:complete", {
            wave: 0,
            name: "ingest",
            state: { ...this.state },
        });
    }
    /**
     * Run a single wave: spawn all agents concurrently and collect results.
     */
    async runWave(wave, waveNum) {
        const agentPromises = wave.agents.map(async (role) => {
            const prompt = this.buildAgentPrompt(role);
            const config = this.agentConfigs[role] ?? {};
            const provider = config.provider ?? this.provider;
            const subCtx = this.context.createSubContext(`wave${waveNum}_${role}`, ROLE_PROMPTS[role] ?? `You are a ${role} agent. Return structured JSON.`);
            // Inject SharedState into the agent's context
            subCtx.addMessage("user", prompt);
            const response = await this.orchestrator.complete(provider, subCtx.getMessagesForApi());
            // Parse and validate against contract
            const parsed = parseAgentResponse(response.content);
            const contract = CONTRACT_REGISTRY[role];
            if (parsed && contract) {
                const validation = contract.safeParse(parsed);
                if (validation.success) {
                    return {
                        role,
                        data: validation.data,
                        raw: response.content,
                        valid: true,
                        usage: response.usage,
                    };
                }
                // Contract violation -- retry once with reminder
                this.emit("contract:violation", {
                    role,
                    wave: waveNum,
                    errors: validation.error.issues,
                });
                const retryCtx = this.context.createSubContext(`wave${waveNum}_${role}_retry`, ROLE_PROMPTS[role]);
                retryCtx.addMessage("user", prompt);
                retryCtx.addMessage("assistant", response.content);
                retryCtx.addMessage("user", `Your response did not match the required contract. Missing or invalid fields: ${validation.error.issues.map((i) => i.path.join(".") + ": " + i.message).join("; ")}.\nPlease return a corrected JSON object with ALL required fields.`);
                const retryResponse = await this.orchestrator.complete(provider, retryCtx.getMessagesForApi());
                const retryParsed = parseAgentResponse(retryResponse.content);
                if (retryParsed) {
                    const retryValidation = contract.safeParse(retryParsed);
                    if (retryValidation.success) {
                        return {
                            role,
                            data: retryValidation.data,
                            raw: retryResponse.content,
                            valid: true,
                            retried: true,
                            usage: retryResponse.usage,
                        };
                    }
                }
                // Second failure -- use partial data with nulls
                return {
                    role,
                    data: parsed,
                    raw: response.content,
                    valid: false,
                    contractErrors: validation.error.issues,
                    usage: response.usage,
                };
            }
            // No contract or couldn't parse -- return raw
            return {
                role,
                data: parsed ?? { raw_response: response.content },
                raw: response.content,
                valid: !contract,
                usage: response.usage,
            };
        });
        const results = await Promise.allSettled(agentPromises);
        return results.map((r, i) => {
            if (r.status === "fulfilled") {
                return r.value;
            }
            return {
                role: wave.agents[i],
                data: null,
                raw: "",
                valid: false,
                error: r.reason instanceof Error ? r.reason.message : String(r.reason),
            };
        });
    }
    /**
     * Build the prompt for an agent, including current SharedState.
     */
    buildAgentPrompt(role) {
        const stateJson = JSON.stringify({
            problem_statement: this.state.problem_statement,
            success_criteria: this.state.success_criteria,
            constraints: this.state.constraints,
            assumptions: this.state.assumptions,
            risks: this.state.risks,
            plan: this.state.plan,
            artifacts_to_update: this.state.artifacts_to_update,
        }, null, 2);
        return [
            "=== SHARED STATE ===",
            stateJson,
            "",
            "=== YOUR TASK ===",
            `Analyze the shared state above and produce your output as a JSON object.`,
            `Follow your role contract exactly. Return ONLY valid JSON.`,
        ].join("\n");
    }
    /**
     * Deterministic merge: dedup, resolve conflicts, update SharedState.
     */
    merge(waveName, results) {
        const audit = {
            wave: waveName,
            agents: results.map((r) => r.role),
            deduped: [],
            conflicts: [],
            merged: [],
        };
        const validResults = results.filter((r) => r.data != null);
        switch (waveName) {
            case "analysis":
                this.mergeAnalysis(validResults, audit);
                break;
            case "plan_validate_optimize":
                this.mergePlanValidateOptimize(validResults, audit);
                break;
            case "execution":
                this.mergeExecution(validResults, audit);
                break;
            case "finalize":
                this.mergeFinalize(validResults, audit);
                break;
            default:
                // Generic merge: collect all data under wave_outputs
                this.state.wave_outputs[waveName] = validResults.map((r) => ({
                    role: r.role,
                    data: r.data,
                }));
        }
        return audit;
    }
    /** Merge Wave 1: Analysis outputs */
    mergeAnalysis(results, audit) {
        const allInsights = [];
        const allConstraints = [];
        const allAssumptions = [];
        const allRisks = [];
        const allRecommendations = [];
        for (const r of results) {
            const d = r.data;
            if (d.key_insights)
                allInsights.push(...d.key_insights);
            if (d.constraints_found)
                allConstraints.push(...d.constraints_found);
            if (d.assumptions)
                allAssumptions.push(...d.assumptions);
            if (d.risks)
                allRisks.push(...d.risks);
            if (d.recommendations_for_next_wave)
                allRecommendations.push(...d.recommendations_for_next_wave);
        }
        const dedupedInsights = dedup(allInsights);
        audit.deduped.push(`insights: ${allInsights.length} → ${dedupedInsights.length}`);
        // Update SharedState
        this.state.constraints = dedup([...this.state.constraints, ...allConstraints]);
        this.state.assumptions = dedup([...this.state.assumptions, ...allAssumptions]);
        this.state.risks = dedup([...this.state.risks, ...allRisks]);
        this.state.wave_outputs.analysis = {
            insights: dedupedInsights,
            recommendations: dedup(allRecommendations),
        };
        audit.merged.push("constraints", "assumptions", "risks", "insights");
    }
    /** Merge Wave 2: Plan + Validate + Optimize outputs */
    mergePlanValidateOptimize(results, audit) {
        const plannerResult = results.find((r) => r.role === "planner");
        const validatorResult = results.find((r) => r.role === "validator");
        const optimizerResult = results.find((r) => r.role === "optimizer");
        // Plan from planner
        if (plannerResult?.data?.step_by_step_plan) {
            this.state.plan = plannerResult.data.step_by_step_plan;
            this.state.artifacts_to_update = dedup([
                ...this.state.artifacts_to_update,
                ...(plannerResult.data.deliverables ?? []),
            ]);
            audit.merged.push("plan", "deliverables");
        }
        // Risks from validator
        if (validatorResult?.data) {
            const vd = validatorResult.data;
            if (vd.edge_cases) {
                this.state.risks = dedup([
                    ...this.state.risks,
                    ...vd.edge_cases,
                ]);
            }
            if (vd.risk_register) {
                const riskStrings = vd.risk_register.map((r) => `[${r.severity}] ${r.risk}: ${r.mitigation}`);
                this.state.risks = dedup([...this.state.risks, ...riskStrings]);
            }
            audit.merged.push("validator_risks");
        }
        // Simplifications from optimizer
        if (optimizerResult?.data?.simplifications) {
            // Apply optimizer suggestions to the plan description
            this.state.wave_outputs.optimization = {
                simplifications: optimizerResult.data.simplifications,
                modularization: optimizerResult.data.modularization_suggestions ?? [],
            };
            audit.merged.push("optimizer_simplifications");
        }
        // Check conflicts between validator and planner
        if (validatorResult?.data?.contradictions_or_gaps?.length > 0) {
            for (const gap of validatorResult.data.contradictions_or_gaps) {
                audit.conflicts.push(`validator found gap: ${gap}`);
            }
        }
        this.state.wave_outputs.readiness_score = validatorResult?.data?.readiness_score ?? null;
    }
    /** Merge Wave 3: Execution outputs */
    mergeExecution(results, audit) {
        const outputs = [];
        for (const r of results) {
            if (r.data?.concrete_output) {
                outputs.push({
                    role: r.role,
                    output: r.data.concrete_output,
                    integration_steps: r.data.integration_steps ?? [],
                    tests: r.data.tests_or_checks ?? [],
                });
            }
        }
        this.state.wave_outputs.execution = outputs;
        this.state.final_answer_outline = outputs
            .map((o) => o.output)
            .join("\n\n---\n\n");
        audit.merged.push("execution_outputs");
    }
    /** Merge Wave 4: Finalize outputs */
    mergeFinalize(results, audit) {
        const monitorResult = results.find((r) => r.role === "monitor");
        const reporterResult = results.find((r) => r.role === "reporter");
        const cleanerResult = results.find((r) => r.role === "cleaner");
        this.state.wave_outputs.monitor = monitorResult?.data ?? null;
        this.state.wave_outputs.reporter = reporterResult?.data ?? null;
        this.state.wave_outputs.cleaner = cleanerResult?.data ?? null;
        audit.merged.push("monitor", "reporter", "cleaner");
        // Check if monitor passed
        if (monitorResult?.data?.verdict === "fail") {
            audit.conflicts.push("Monitor verdict: FAIL -- remaining risks not addressed");
        }
    }
    /**
     * Build the final answer from wave outputs.
     *
     * Priority: cleaner > reporter > execution outline > raw state.
     */
    buildFinalAnswer() {
        const cleaner = this.state.wave_outputs?.cleaner;
        if (cleaner?.cleaned_output) {
            return cleaner.cleaned_output;
        }
        const reporter = this.state.wave_outputs?.reporter;
        if (reporter?.final_answer) {
            return reporter.final_answer;
        }
        if (this.state.final_answer_outline) {
            return this.state.final_answer_outline;
        }
        // Fallback: summarize the state
        return [
            `## Problem\n${this.state.problem_statement}`,
            this.state.plan.length > 0
                ? `## Plan\n${this.state.plan.map((s, i) => `${i + 1}. ${s}`).join("\n")}`
                : "",
            this.state.risks.length > 0
                ? `## Risks\n${this.state.risks.map((r) => `- ${r}`).join("\n")}`
                : "",
        ]
            .filter(Boolean)
            .join("\n\n");
    }
    /** Map wave number to operation phase for progress events */
    waveToPhase(wave) {
        switch (wave) {
            case 1:
                return OperationPhase.ANALYZING;
            case 2:
                return OperationPhase.PLANNING;
            case 3:
                return OperationPhase.IMPLEMENTING;
            case 4:
                return OperationPhase.REVIEWING;
            default:
                return OperationPhase.ANALYZING;
        }
    }
    /**
     * Adaptive wave selection based on intent type.
     *
     * - Documentation tasks skip Execution wave
     * - Simple code tasks skip Analysis wave
     * - Research tasks skip Execution wave
     */
    selectWaves() {
        if (!this.intentType)
            return this.waves;
        const skipMap = {
            docs: ["execution"],
            research: ["execution"],
            code: [],
            debug: [],
            test: ["analysis"],
            review: ["execution"],
            plan: ["execution"],
            orchestrator: [],
            team: [],
        };
        const skipWaves = skipMap[this.intentType] ?? [];
        if (skipWaves.length === 0)
            return this.waves;
        const filtered = this.waves.filter((w) => !skipWaves.includes(w.name));
        // Always keep at least finalize
        if (filtered.length === 0)
            return this.waves;
        this.emit("adaptive:skip", {
            intent: this.intentType,
            skipped: skipWaves,
            remaining: filtered.map((w) => w.name),
        });
        return filtered;
    }
    /**
     * Build a cache key from wave name and current SharedState hash.
     */
    buildCacheKey(waveName) {
        const stateStr = JSON.stringify({
            problem_statement: this.state.problem_statement,
            constraints: this.state.constraints,
            plan: this.state.plan,
        });
        return `${waveName}:${contentHash(stateStr)}`;
    }
    /** Get total tokens used across all waves */
    getTokensUsed() {
        return this.tokensUsed;
    }
    /** Get the current SharedState (for inspection/debugging) */
    getState() {
        return { ...this.state };
    }
    /** Get the audit trail */
    getAuditTrail() {
        return [...this.auditTrail];
    }
}
/**
 * In-memory result cache for sub-agent wave outputs.
 *
 * Keyed by SharedState hash so re-runs with identical state
 * skip completed waves.
 */
export class ChainCache {
    entries = new Map();
    maxSize;
    constructor(maxSize = 100) {
        this.maxSize = maxSize;
    }
    get(key) {
        const entry = this.entries.get(key);
        if (!entry)
            return null;
        return entry;
    }
    set(key, value) {
        // Evict oldest if at capacity
        if (this.entries.size >= this.maxSize) {
            const firstKey = this.entries.keys().next().value;
            if (firstKey)
                this.entries.delete(firstKey);
        }
        this.entries.set(key, value);
    }
    /** Invalidate all entries */
    clear() {
        const count = this.entries.size;
        this.entries.clear();
        return count;
    }
    /** Get cache size */
    get size() {
        return this.entries.size;
    }
}
//# sourceMappingURL=chain.js.map
