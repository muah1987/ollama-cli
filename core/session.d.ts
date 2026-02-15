/**
 * Session persistence module.
 *
 * Ports the Python model/session.py into TypeScript.
 * Manages session state with save/load for continuity across runs,
 * QARIN.md project context seeding, and session summary tracking.
 */
import type { SessionStatus } from "../types/agent.js";
import { ContextManager } from "./context.js";
import { TokenCounter } from "./tokens.js";
/**
 * Session manager with persistence and QARIN.md integration.
 *
 * Coordinates the ContextManager and TokenCounter, handles QARIN.md
 * project context seeding, and provides save/load for continuity.
 */
export declare class Session {
    readonly sessionId: string;
    readonly model: string;
    readonly provider: string;
    readonly context: ContextManager;
    readonly tokenCounter: TokenCounter;
    readonly hooksEnabled: boolean;
    private startTime;
    private endTime;
    private _messageCount;
    constructor(options?: {
        sessionId?: string;
        model?: string;
        provider?: string;
        context?: ContextManager;
        tokenCounter?: TokenCounter;
        hooksEnabled?: boolean;
    });
    get messageCount(): number;
    /** Start the session, loading QARIN.md context if available */
    start(): Promise<void>;
    /** Record a message exchange */
    recordMessage(): void;
    /** End the session and return a summary */
    end(): Promise<Record<string, unknown>>;
    /** Get current session status */
    getStatus(): SessionStatus;
    /** Save session state to a JSON file */
    save(path?: string): Promise<string>;
    /** Load a session from a JSON file */
    static load(sessionId: string, path?: string): Promise<Session>;
    /** Format a duration in seconds to human-readable string */
    static formatDuration(seconds: number): string;
    /** Build session summary */
    private buildSummary;
    /** Look for QARIN.md in the current directory and parent dirs up to repo root */
    private findQarinMd;
    /** Append a session summary to QARIN.md */
    private appendToQarinMd;
}
//# sourceMappingURL=session.d.ts.map