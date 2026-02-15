/**
 * Unit tests for chain types and utilities.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
    AnalyzerContract,
    PlannerContract,
    ValidatorContract,
    ExecutorContract,
    MonitorContract,
    ReporterContract,
    CleanerContract,
    CONTRACT_REGISTRY,
    ROLE_PROMPTS,
    DEFAULT_WAVES,
    SharedStateSchema,
    createEmptySharedState,
} from "../types/chain.js";
import { ChainCache } from "../core/chain.js";

describe("Chain Types", () => {
    it("creates empty SharedState", () => {
        const state = createEmptySharedState();
        assert.equal(state.problem_statement, "");
        assert.deepEqual(state.success_criteria, []);
        assert.deepEqual(state.constraints, []);
        assert.deepEqual(state.plan, []);
        assert.deepEqual(state.wave_outputs, {});
    });

    it("validates SharedState schema", () => {
        const state = createEmptySharedState();
        const result = SharedStateSchema.safeParse(state);
        assert.equal(result.success, true);
    });

    it("validates Analyzer contract", () => {
        const valid = {
            key_insights: ["insight1"],
            constraints_found: ["c1"],
            assumptions: ["a1"],
            risks: ["r1"],
            questions_to_clarify: [],
            recommendations_for_next_wave: ["rec1"],
        };
        const result = AnalyzerContract.safeParse(valid);
        assert.equal(result.success, true);
    });

    it("rejects invalid Analyzer contract", () => {
        const invalid = { key_insights: "not an array" };
        const result = AnalyzerContract.safeParse(invalid);
        assert.equal(result.success, false);
    });

    it("validates Planner contract", () => {
        const valid = {
            step_by_step_plan: ["step1"],
            deliverables: ["d1"],
            dependencies_tools_needed: [],
            acceptance_checks: ["check1"],
            recommendations_for_execution: [],
        };
        const result = PlannerContract.safeParse(valid);
        assert.equal(result.success, true);
    });

    it("validates Validator contract", () => {
        const valid = {
            contradictions_or_gaps: [],
            risk_register: [{ risk: "r", severity: "medium", mitigation: "m" }],
            edge_cases: [],
            must_not_do: [],
            readiness_score: 85,
        };
        const result = ValidatorContract.safeParse(valid);
        assert.equal(result.success, true);
    });

    it("rejects invalid readiness_score", () => {
        const invalid = {
            contradictions_or_gaps: [],
            risk_register: [],
            edge_cases: [],
            must_not_do: [],
            readiness_score: 150,
        };
        const result = ValidatorContract.safeParse(invalid);
        assert.equal(result.success, false);
    });

    it("validates Monitor contract", () => {
        const valid = {
            criteria_met: [{ criterion: "works", met: true, evidence: "test passes" }],
            remaining_risks: [],
            verdict: "pass",
        };
        const result = MonitorContract.safeParse(valid);
        assert.equal(result.success, true);
    });

    it("has all roles in contract registry", () => {
        const roles = Object.keys(CONTRACT_REGISTRY);
        assert.ok(roles.includes("analyzer_a"));
        assert.ok(roles.includes("planner"));
        assert.ok(roles.includes("validator"));
        assert.ok(roles.includes("executor_1"));
        assert.ok(roles.includes("monitor"));
        assert.ok(roles.includes("reporter"));
        assert.ok(roles.includes("cleaner"));
    });

    it("has prompts for all roles", () => {
        const roles = Object.keys(ROLE_PROMPTS);
        assert.ok(roles.length >= 10);
        for (const role of roles) {
            assert.ok(ROLE_PROMPTS[role].length > 50);
        }
    });

    it("has 4 default waves", () => {
        assert.equal(DEFAULT_WAVES.length, 4);
        assert.equal(DEFAULT_WAVES[0].name, "analysis");
        assert.equal(DEFAULT_WAVES[3].name, "finalize");
    });
});

describe("ChainCache", () => {
    it("stores and retrieves entries", () => {
        const cache = new ChainCache();
        cache.set("key1", { results: [], audit: {} });
        const entry = cache.get("key1");
        assert.ok(entry);
        assert.deepEqual(entry.results, []);
    });

    it("returns null for missing keys", () => {
        const cache = new ChainCache();
        assert.equal(cache.get("missing"), null);
    });

    it("evicts oldest on overflow", () => {
        const cache = new ChainCache(2);
        cache.set("a", { results: [1] });
        cache.set("b", { results: [2] });
        cache.set("c", { results: [3] });
        assert.equal(cache.size, 2);
        assert.equal(cache.get("a"), null);
        assert.ok(cache.get("b"));
    });

    it("clears all entries", () => {
        const cache = new ChainCache();
        cache.set("x", {});
        cache.set("y", {});
        const count = cache.clear();
        assert.equal(count, 2);
        assert.equal(cache.size, 0);
    });
});
