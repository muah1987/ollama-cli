/**
 * Token counter with cost estimation.
 *
 * Ports the Python runner/token_counter.py into TypeScript.
 * Real-time token tracking with cost estimation across providers.
 */
import { Provider } from "../types/message.js";
/** Cost per million tokens (input/output) by provider */
const COST_PER_MILLION = {
    [Provider.OLLAMA]: { input: 0.0, output: 0.0 },
    [Provider.ANTHROPIC]: { input: 3.0, output: 15.0 },
    [Provider.OPENAI]: { input: 1.0, output: 2.0 },
    claude: { input: 3.0, output: 15.0 },
    gemini: { input: 1.25, output: 5.0 },
    google: { input: 1.25, output: 5.0 },
    codex: { input: 2.5, output: 10.0 },
};
/**
 * Real-time token counter with cost estimation.
 *
 * Tracks prompt and completion tokens across a session, computes
 * generation speed, and estimates cost based on provider pricing.
 */
export class TokenCounter {
    _provider;
    _promptTokens = 0;
    _completionTokens = 0;
    _tokensPerSecond = 0;
    _contextUsed = 0;
    _contextMax;
    _costEstimate = 0;
    constructor(provider = "ollama", contextMax = 4096) {
        this._provider = provider;
        this._contextMax = contextMax;
    }
    /** Combined prompt + completion tokens for the session */
    get totalTokens() {
        return this._promptTokens + this._completionTokens;
    }
    get promptTokens() {
        return this._promptTokens;
    }
    get completionTokens() {
        return this._completionTokens;
    }
    get tokensPerSecond() {
        return this._tokensPerSecond;
    }
    get contextUsed() {
        return this._contextUsed;
    }
    get contextMax() {
        return this._contextMax;
    }
    get costEstimate() {
        return this._costEstimate;
    }
    get provider() {
        return this._provider;
    }
    /** Update counters from a provider response */
    update(usage, durationMs) {
        this._promptTokens += usage.promptTokens;
        this._completionTokens += usage.completionTokens;
        if (durationMs && durationMs > 0 && usage.completionTokens > 0) {
            this._tokensPerSecond = Math.round((usage.completionTokens / (durationMs / 1000)) * 100) / 100;
        }
        // Update context-used to reflect the latest prompt size
        if (usage.promptTokens > 0) {
            this._contextUsed = usage.promptTokens;
        }
        this._costEstimate = this.estimateCost();
    }
    /** Update context window tracking values */
    setContext(used, maxTokens) {
        this._contextUsed = used;
        this._contextMax = maxTokens;
    }
    /** Format a display string for the status bar */
    formatDisplay() {
        const used = this._contextUsed.toLocaleString();
        const cap = this._contextMax.toLocaleString();
        const speed = this._tokensPerSecond.toFixed(1);
        const cost = this._costEstimate > 0
            ? `$${this._costEstimate.toFixed(4)}`
            : "$0.00";
        return `[tok: ${used}/${cap} | ${speed} tok/s | ${cost}]`;
    }
    /** Return token metrics as a plain object */
    toJSON() {
        return {
            promptTokens: this._promptTokens,
            completionTokens: this._completionTokens,
            totalTokens: this.totalTokens,
            tokensPerSecond: this._tokensPerSecond,
            contextUsed: this._contextUsed,
            contextMax: this._contextMax,
            costEstimate: Math.round(this._costEstimate * 1_000_000) / 1_000_000,
            provider: this._provider,
        };
    }
    /**
     * Recreate a TokenCounter instance from a JSON representation produced by toJSON().
     */
    static fromJSON(json) {
        const provider = json.provider ?? Provider.OLLAMA;
        const counter = new this(provider, json.contextMax);
        counter._promptTokens = Number.isFinite(json.promptTokens) ? json.promptTokens : 0;
        counter._completionTokens = Number.isFinite(json.completionTokens) ? json.completionTokens : 0;
        counter._tokensPerSecond = Number.isFinite(json.tokensPerSecond) ? json.tokensPerSecond : 0;
        counter._contextUsed = Number.isFinite(json.contextUsed) ? json.contextUsed : 0;
        counter._contextMax = Number.isFinite(json.contextMax) ? json.contextMax : 0;
        // Recompute cost estimate from current pricing to keep behavior consistent.
        counter._costEstimate = counter.estimateCost();
        return counter;
    }
    /** Reset all counters to zero */
    reset() {
        this._promptTokens = 0;
        this._completionTokens = 0;
        this._tokensPerSecond = 0;
        this._contextUsed = 0;
        this._costEstimate = 0;
    }
    /** Calculate estimated cost based on provider pricing */
    estimateCost() {
        const key = this._provider.toLowerCase();
        const rates = COST_PER_MILLION[key];
        if (!rates || (rates.input === 0 && rates.output === 0)) {
            return 0;
        }
        const inputCost = (this._promptTokens / 1_000_000) * rates.input;
        const outputCost = (this._completionTokens / 1_000_000) * rates.output;
        return Math.round((inputCost + outputCost) * 1_000_000) / 1_000_000;
    }
}
//# sourceMappingURL=tokens.js.map