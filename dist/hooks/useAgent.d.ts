/**
 * React hook for managing the QarinAgent lifecycle.
 *
 * Provides reactive state for agent phases, streaming output,
 * intent classification, token metrics, and session status.
 */
import type { SessionStatus, ToolResult, IntentResult } from "../types/agent.js";
import type { CLIOptions } from "../types/agent.js";
import { OperationPhase } from "../types/theme.js";
interface UseAgentReturn {
    /** Current operation phase */
    phase: OperationPhase;
    /** Phase details message */
    details: string;
    /** Whether the agent is processing */
    isProcessing: boolean;
    /** Accumulated streaming output */
    streamOutput: string;
    /** Session status snapshot */
    status: SessionStatus | null;
    /** Last classified intent */
    intent: IntentResult | null;
    /** Token display string */
    tokenDisplay: string;
    /** Error if any */
    error: Error | null;
    /** Send a message to the agent */
    sendMessage: (message: string) => Promise<void>;
    /** Execute a tool */
    runTool: (name: string, args: Record<string, unknown>) => Promise<ToolResult | null>;
    /** End the session */
    endSession: () => Promise<void>;
}
export declare function useAgent(options: CLIOptions): UseAgentReturn;
export {};
//# sourceMappingURL=useAgent.d.ts.map