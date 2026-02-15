/**
 * Token counter with cost estimation.
 *
 * Ports the Python runner/token_counter.py into TypeScript.
 * Real-time token tracking with cost estimation across providers.
 */
import type { TokenUsage } from "../types/message.js";
/** Metrics extracted from a provider response */
export interface ResponseMetrics {
    promptTokens: number;
    completionTokens: number;
    tokensPerSecond: number;
}
/**
 * Real-time token counter with cost estimation.
 *
 * Tracks prompt and completion tokens across a session, computes
 * generation speed, and estimates cost based on provider pricing.
 */
export declare class TokenCounter {
    private _provider;
    private _promptTokens;
    private _completionTokens;
    private _tokensPerSecond;
    private _contextUsed;
    private _contextMax;
    private _costEstimate;
    constructor(provider?: string, contextMax?: number);
    /** Combined prompt + completion tokens for the session */
    get totalTokens(): number;
    get promptTokens(): number;
    get completionTokens(): number;
    get tokensPerSecond(): number;
    get contextUsed(): number;
    get contextMax(): number;
    get costEstimate(): number;
    get provider(): string;
    /** Update counters from a provider response */
    update(usage: TokenUsage, durationMs?: number): void;
    /** Update context window tracking values */
    setContext(used: number, maxTokens: number): void;
    /** Format a display string for the status bar */
    formatDisplay(): string;
    /** Return token metrics as a plain object */
    toJSON(): Record<string, unknown>;
    /**
     * Recreate a TokenCounter instance from a JSON representation produced by toJSON().
     */
    static fromJSON(json: {
        promptTokens: number;
        completionTokens: number;
        totalTokens?: number;
        tokensPerSecond: number;
        contextUsed: number;
        contextMax: number;
        costEstimate?: number;
        provider: string;
    }): TokenCounter;
    /** Reset all counters to zero */
    reset(): void;
    /** Calculate estimated cost based on provider pricing */
    private estimateCost;
}
//# sourceMappingURL=tokens.d.ts.map