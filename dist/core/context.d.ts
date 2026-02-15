/**
 * Context gathering module.
 *
 * Ports the Python ContextManager into TypeScript with sub-context support.
 */
import type { Message } from "../types/message.js";
import type { ContextUsage } from "../types/agent.js";
/**
 * Manages conversation context with auto-compaction.
 *
 * Ports the Python ContextManager class with sub-context hierarchy
 * for sub-agent orchestration.
 */
export declare class ContextManager {
    private readonly maxContextLength;
    private readonly compactThreshold;
    private readonly autoCompact;
    private readonly keepLastN;
    private readonly contextId?;
    private readonly parentContext?;
    private messages;
    private systemMessage;
    private totalPromptTokens;
    private totalCompletionTokens;
    private estimatedContextTokens;
    private subContexts;
    constructor(maxContextLength?: number, compactThreshold?: number, autoCompact?: boolean, keepLastN?: number, contextId?: string | undefined, parentContext?: ContextManager | undefined);
    /** Set or update the system message */
    setSystemMessage(prompt: string): void;
    /** Add a message to the conversation history */
    addMessage(role: Message["role"], content: string, options?: {
        toolCalls?: Message["tool_calls"];
        toolCallId?: string;
    }): void;
    /** Check if context compaction is needed */
    shouldCompact(): boolean;
    /** Compact the conversation by summarizing older messages */
    compact(): void;
    /** Get messages formatted for API calls */
    getMessagesForApi(): Message[];
    /** Get context window usage statistics */
    getContextUsage(): ContextUsage;
    /** Update token metrics from a provider response */
    updateMetrics(promptTokens: number, completionTokens: number): void;
    /** Create a sub-context for sub-agent orchestration */
    createSubContext(contextId: string, systemMessage?: string): ContextManager;
    /** Get a sub-context by ID */
    getSubContext(contextId: string): ContextManager | undefined;
    /** Get the total number of messages */
    get messageCount(): number;
    /** Get total prompt tokens consumed */
    get promptTokens(): number;
    /** Get total completion tokens consumed */
    get completionTokens(): number;
    /** Serialize context to JSON for persistence */
    toJSON(): Record<string, unknown>;
    /** Restore context from serialized JSON */
    static fromJSON(data: Record<string, unknown>): ContextManager;
    /** Estimate current token usage */
    private estimateCurrentTokens;
}
//# sourceMappingURL=context.d.ts.map