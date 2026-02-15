/**
 * React hook for sub-agent orchestration state.
 */
import type { SharedState } from "../types/agent.js";
import type { SubagentWaveEvent } from "../types/theme.js";
import { ContextManager } from "../core/context.js";
import { ModelOrchestrator } from "../core/models.js";
interface UseSubagentsReturn {
    /** Whether orchestration is in progress */
    isOrchestrating: boolean;
    /** Current wave number (1-4) */
    currentWave: number;
    /** Wave events for tracking progress */
    waveEvents: SubagentWaveEvent[];
    /** Final shared state result */
    result: SharedState | null;
    /** Error if any */
    error: Error | null;
    /** Start orchestrating a task */
    orchestrate: (task: string) => Promise<void>;
}
export declare function useSubagents(orchestrator: ModelOrchestrator, context: ContextManager): UseSubagentsReturn;
export {};
//# sourceMappingURL=useSubagents.d.ts.map