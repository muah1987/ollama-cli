/**
 * Sub-agent orchestration module.
 *
 * Ports the Python chain_controller.py and Llama Doctor 4-wave
 * delegation pattern into TypeScript.
 */
import { EventEmitter } from "node:events";
import { Provider } from "../types/message.js";
import type { SharedState } from "../types/agent.js";
import { ContextManager } from "./context.js";
import { ModelOrchestrator } from "./models.js";
/** Configuration for a sub-agent */
interface SubagentConfig {
    name: string;
    systemPrompt: string;
    provider: Provider;
    model: string;
}
/**
 * Sub-agent orchestrator implementing the 4-wave delegation pattern.
 *
 * Wave 1: Diagnostic - Analyze the problem (🔍)
 * Wave 2: Analysis  - Find root cause (🧠)
 * Wave 3: Solution  - Generate fix (💊)
 * Wave 4: Verify    - Test the solution (✅)
 */
export declare class SubagentOrchestrator extends EventEmitter {
    private diagnosticAgent;
    private analysisAgent;
    private solutionAgent;
    private verificationAgent;
    private context;
    constructor(orchestrator: ModelOrchestrator, context: ContextManager, configs?: Partial<Record<string, SubagentConfig>>);
    /** Execute the full 4-wave orchestration */
    orchestrate(task: string): Promise<SharedState>;
    /** Emit a sub-agent wave event */
    private emitWaveEvent;
}
export {};
//# sourceMappingURL=subagents.d.ts.map