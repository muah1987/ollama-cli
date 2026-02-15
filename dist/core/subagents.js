/**
 * Sub-agent orchestration module.
 *
 * Ports the Python chain_controller.py and Llama Doctor 4-wave
 * delegation pattern into TypeScript.
 */
import { EventEmitter } from "node:events";
import { Provider } from "../types/message.js";
import { OperationPhase } from "../types/theme.js";
/**
 * Diagnostic agent - Wave 1: Analyze the problem.
 */
class DiagnosticAgent {
    orchestrator;
    config;
    constructor(orchestrator, config) {
        this.orchestrator = orchestrator;
        this.config = config;
    }
    async analyze(task, context) {
        const subCtx = context.createSubContext("diagnostic", this.config.systemPrompt);
        subCtx.addMessage("user", `Analyze this task and identify the key issues:\n\n${task}`);
        const response = await this.orchestrator.complete(this.config.provider, subCtx.getMessagesForApi());
        return {
            analysis: response.content,
            model: response.model,
            provider: response.provider,
        };
    }
}
/**
 * Analysis agent - Wave 2: Find root cause.
 */
class AnalysisAgent {
    orchestrator;
    config;
    constructor(orchestrator, config) {
        this.orchestrator = orchestrator;
        this.config = config;
    }
    async findCause(symptoms, context) {
        const subCtx = context.createSubContext("analysis", this.config.systemPrompt);
        subCtx.addMessage("user", `Given this analysis, identify the root cause:\n\n${JSON.stringify(symptoms, null, 2)}`);
        const response = await this.orchestrator.complete(this.config.provider, subCtx.getMessagesForApi());
        return {
            rootCause: response.content,
            model: response.model,
            provider: response.provider,
        };
    }
}
/**
 * Solution agent - Wave 3: Generate fix.
 */
class SolutionAgent {
    orchestrator;
    config;
    constructor(orchestrator, config) {
        this.orchestrator = orchestrator;
        this.config = config;
    }
    async generate(rootCause, context) {
        const subCtx = context.createSubContext("solution", this.config.systemPrompt);
        subCtx.addMessage("user", `Generate a solution for this root cause:\n\n${JSON.stringify(rootCause, null, 2)}`);
        const response = await this.orchestrator.complete(this.config.provider, subCtx.getMessagesForApi());
        return {
            solution: response.content,
            model: response.model,
            provider: response.provider,
        };
    }
}
/**
 * Verification agent - Wave 4: Test the fix.
 */
class VerificationAgent {
    orchestrator;
    config;
    constructor(orchestrator, config) {
        this.orchestrator = orchestrator;
        this.config = config;
    }
    async test(solution, context) {
        const subCtx = context.createSubContext("verification", this.config.systemPrompt);
        subCtx.addMessage("user", `Verify and test this solution:\n\n${JSON.stringify(solution, null, 2)}`);
        const response = await this.orchestrator.complete(this.config.provider, subCtx.getMessagesForApi());
        return {
            verified: true,
            verification: response.content,
            model: response.model,
            provider: response.provider,
        };
    }
}
/**
 * Sub-agent orchestrator implementing the 4-wave delegation pattern.
 *
 * Wave 1: Diagnostic - Analyze the problem (🔍)
 * Wave 2: Analysis  - Find root cause (🧠)
 * Wave 3: Solution  - Generate fix (💊)
 * Wave 4: Verify    - Test the solution (✅)
 */
export class SubagentOrchestrator extends EventEmitter {
    diagnosticAgent;
    analysisAgent;
    solutionAgent;
    verificationAgent;
    context;
    constructor(orchestrator, context, configs) {
        super();
        this.context = context;
        const defaultConfig = {
            name: "default",
            systemPrompt: "You are a helpful AI assistant.",
            provider: Provider.OLLAMA,
            model: "qwen2.5",
        };
        this.diagnosticAgent = new DiagnosticAgent(orchestrator, configs?.diagnostic ?? {
            ...defaultConfig,
            name: "diagnostic",
            systemPrompt: "You are a diagnostic agent. Analyze the task and identify key issues, dependencies, and constraints.",
        });
        this.analysisAgent = new AnalysisAgent(orchestrator, configs?.analysis ?? {
            ...defaultConfig,
            name: "analysis",
            systemPrompt: "You are an analysis agent. Given diagnostic results, identify the root cause and underlying patterns.",
        });
        this.solutionAgent = new SolutionAgent(orchestrator, configs?.solution ?? {
            ...defaultConfig,
            name: "solution",
            systemPrompt: "You are a solution agent. Generate concrete, actionable fixes with code examples.",
        });
        this.verificationAgent = new VerificationAgent(orchestrator, configs?.verification ?? {
            ...defaultConfig,
            name: "verification",
            systemPrompt: "You are a verification agent. Test solutions for correctness, edge cases, and regressions.",
        });
    }
    /** Execute the full 4-wave orchestration */
    async orchestrate(task) {
        const state = {
            userInput: task,
            constraints: [],
            analysisResults: {},
            plan: {},
            executionOutputs: [],
            status: "started",
        };
        try {
            // Wave 1: Diagnostic (🔍)
            this.emitWaveEvent(1, "diagnostic", "started");
            this.emit("progress", {
                phase: OperationPhase.ANALYZING,
                details: "Wave 1: Diagnostic analysis",
            });
            const symptoms = await this.diagnosticAgent.analyze(task, this.context);
            state.analysisResults = symptoms;
            this.emitWaveEvent(1, "diagnostic", "completed");
            // Wave 2: Root Cause (🧠)
            this.emitWaveEvent(2, "analysis", "started");
            this.emit("progress", {
                phase: OperationPhase.PLANNING,
                details: "Wave 2: Root cause analysis",
            });
            const rootCause = await this.analysisAgent.findCause(symptoms, this.context);
            state.plan = rootCause;
            this.emitWaveEvent(2, "analysis", "completed");
            // Wave 3: Treatment (💊)
            this.emitWaveEvent(3, "solution", "started");
            this.emit("progress", {
                phase: OperationPhase.IMPLEMENTING,
                details: "Wave 3: Generating solution",
            });
            const solution = await this.solutionAgent.generate(rootCause, this.context);
            state.executionOutputs.push(solution);
            this.emitWaveEvent(3, "solution", "completed");
            // Wave 4: Verification (✅)
            this.emitWaveEvent(4, "verification", "started");
            this.emit("progress", {
                phase: OperationPhase.TESTING,
                details: "Wave 4: Verifying solution",
            });
            const verified = await this.verificationAgent.test(solution, this.context);
            state.executionOutputs.push(verified);
            this.emitWaveEvent(4, "verification", "completed");
            state.status = "completed";
            this.emit("progress", {
                phase: OperationPhase.COMPLETE,
                details: "All waves completed successfully",
            });
        }
        catch (err) {
            state.status = "failed";
            this.emit("progress", {
                phase: OperationPhase.ERROR,
                details: `Orchestration failed: ${err instanceof Error ? err.message : String(err)}`,
            });
        }
        return state;
    }
    /** Emit a sub-agent wave event */
    emitWaveEvent(wave, name, status) {
        this.emit("subagent:wave", { wave, name, status });
    }
}
//# sourceMappingURL=subagents.js.map