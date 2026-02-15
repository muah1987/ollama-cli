/**
 * Chain controller types, sub-agent contracts, and Zod schemas.
 *
 * Defines the SharedState that flows between waves, per-role
 * return contracts enforced with Zod, wave/chain configuration,
 * and the merge policy interface.
 */
import { z } from "zod";
// ─── Sub-agent Return Contracts ────────────────────────────────
/** Analyzer contract (Wave 1) */
export const AnalyzerContract = z.object({
    key_insights: z.array(z.string()),
    constraints_found: z.array(z.string()),
    assumptions: z.array(z.string()),
    risks: z.array(z.string()),
    questions_to_clarify: z.array(z.string()),
    recommendations_for_next_wave: z.array(z.string()),
});
/** Planner contract (Wave 2) */
export const PlannerContract = z.object({
    step_by_step_plan: z.array(z.string()),
    deliverables: z.array(z.string()),
    dependencies_tools_needed: z.array(z.string()),
    acceptance_checks: z.array(z.string()),
    recommendations_for_execution: z.array(z.string()),
});
/** Validator contract (Wave 2) */
export const ValidatorContract = z.object({
    contradictions_or_gaps: z.array(z.string()),
    risk_register: z.array(z.object({
        risk: z.string(),
        severity: z.enum(["low", "medium", "high", "critical"]),
        mitigation: z.string(),
    })),
    edge_cases: z.array(z.string()),
    must_not_do: z.array(z.string()),
    readiness_score: z.number().min(0).max(100),
});
/** Optimizer contract (Wave 2) */
export const OptimizerContract = z.object({
    simplifications: z.array(z.string()),
    modularization_suggestions: z.array(z.string()),
    clarity_improvements: z.array(z.string()),
    performance_considerations: z.array(z.string()),
});
/** Executor contract (Wave 3) */
export const ExecutorContract = z.object({
    concrete_output: z.string(),
    integration_steps: z.array(z.string()),
    tests_or_checks: z.array(z.string()),
});
/** Monitor contract (Wave 4) */
export const MonitorContract = z.object({
    criteria_met: z.array(z.object({
        criterion: z.string(),
        met: z.boolean(),
        evidence: z.string(),
    })),
    remaining_risks: z.array(z.string()),
    verdict: z.enum(["pass", "partial", "fail"]),
});
/** Reporter contract (Wave 4) */
export const ReporterContract = z.object({
    final_answer: z.string(),
    summary: z.string(),
    follow_up_suggestions: z.array(z.string()),
});
/** Cleaner contract (Wave 4) */
export const CleanerContract = z.object({
    cleaned_output: z.string(),
    changes_made: z.array(z.string()),
});
// ─── Contract Registry ─────────────────────────────────────────
/** Map of role names to their Zod contract schemas */
export const CONTRACT_REGISTRY = {
    analyzer_a: AnalyzerContract,
    analyzer_b: AnalyzerContract,
    planner: PlannerContract,
    validator: ValidatorContract,
    optimizer: OptimizerContract,
    executor_1: ExecutorContract,
    executor_2: ExecutorContract,
    monitor: MonitorContract,
    reporter: ReporterContract,
    cleaner: CleanerContract,
};
// ─── Role Prompts ──────────────────────────────────────────────
/** System prompts for each sub-agent role */
export const ROLE_PROMPTS = {
    analyzer_a: `ROLE: Analyzer-A (Technical/Architectural)
You analyze requirements from a technical and architectural angle.
Return a JSON object with these exact keys:
- key_insights: array of strings (technical insights)
- constraints_found: array of strings (technical constraints)
- assumptions: array of strings (tagged assumptions)
- risks: array of strings (technical risks)
- questions_to_clarify: array of strings (only if blocking)
- recommendations_for_next_wave: array of strings
Keep it concise. Do not propose a final answer.`,
    analyzer_b: `ROLE: Analyzer-B (UX/Risk/Edge-case)
You analyze requirements from a UX, risk, and edge-case angle.
Return a JSON object with these exact keys:
- key_insights: array of strings (UX and risk insights)
- constraints_found: array of strings (user-facing constraints)
- assumptions: array of strings (tagged assumptions)
- risks: array of strings (UX and business risks)
- questions_to_clarify: array of strings (only if blocking)
- recommendations_for_next_wave: array of strings
Keep it concise. Do not propose a final answer.`,
    planner: `ROLE: Planner
You produce a step-by-step plan from the shared analysis.
Return a JSON object with these exact keys:
- step_by_step_plan: array of strings (ordered steps)
- deliverables: array of strings (what will be produced)
- dependencies_tools_needed: array of strings
- acceptance_checks: array of strings (how to verify done)
- recommendations_for_execution: array of strings`,
    validator: `ROLE: Validator
You check the plan for completeness, contradictions, safety, and constraints.
Return a JSON object with these exact keys:
- contradictions_or_gaps: array of strings
- risk_register: array of objects with { risk, severity, mitigation } where severity is "low"|"medium"|"high"|"critical"
- edge_cases: array of strings
- must_not_do: array of strings (violations to avoid)
- readiness_score: number 0-100 with reasoning`,
    optimizer: `ROLE: Optimizer
You simplify and improve the plan for production readiness.
Return a JSON object with these exact keys:
- simplifications: array of strings
- modularization_suggestions: array of strings
- clarity_improvements: array of strings
- performance_considerations: array of strings`,
    executor_1: `ROLE: Executor-1
You produce concrete outputs (code, specs, configs, templates).
Return a JSON object with these exact keys:
- concrete_output: string (the actual code/spec/config)
- integration_steps: array of strings (how to plug into existing flow)
- tests_or_checks: array of strings`,
    executor_2: `ROLE: Executor-2
You produce complementary outputs or an alternative approach.
Return a JSON object with these exact keys:
- concrete_output: string (the actual code/spec/config)
- integration_steps: array of strings (how to plug into existing flow)
- tests_or_checks: array of strings`,
    monitor: `ROLE: Monitor
You verify final outputs against success criteria from the shared state.
Return a JSON object with these exact keys:
- criteria_met: array of objects with { criterion, met (boolean), evidence }
- remaining_risks: array of strings
- verdict: one of "pass", "partial", "fail"`,
    reporter: `ROLE: Reporter
You produce the final user-facing response.
Return a JSON object with these exact keys:
- final_answer: string (the complete answer for the user)
- summary: string (1-3 sentence summary)
- follow_up_suggestions: array of strings`,
    cleaner: `ROLE: Cleaner
You polish formatting, remove noise and duplicates, and ensure consistency.
Return a JSON object with these exact keys:
- cleaned_output: string (the polished final output)
- changes_made: array of strings (what you cleaned up)`,
};
// ─── Wave Configuration ────────────────────────────────────────
/** Default wave configuration */
export const DEFAULT_WAVES = [
    {
        name: "analysis",
        agents: ["analyzer_a", "analyzer_b"],
    },
    {
        name: "plan_validate_optimize",
        agents: ["planner", "validator", "optimizer"],
    },
    {
        name: "execution",
        agents: ["executor_1", "executor_2"],
    },
    {
        name: "finalize",
        agents: ["monitor", "reporter", "cleaner"],
    },
];
// ─── SharedState Schema ────────────────────────────────────────
/** Zod schema for SharedState validation */
export const SharedStateSchema = z.object({
    problem_statement: z.string(),
    success_criteria: z.array(z.string()),
    constraints: z.array(z.string()),
    assumptions: z.array(z.string()),
    risks: z.array(z.string()),
    plan: z.array(z.string()),
    artifacts_to_update: z.array(z.string()),
    final_answer_outline: z.string(),
    wave_outputs: z.record(z.string(), z.any()).optional(),
});
/** Create an empty SharedState */
export function createEmptySharedState() {
    return {
        problem_statement: "",
        success_criteria: [],
        constraints: [],
        assumptions: [],
        risks: [],
        plan: [],
        artifacts_to_update: [],
        final_answer_outline: "",
        wave_outputs: {},
    };
}
//# sourceMappingURL=chain.js.map
