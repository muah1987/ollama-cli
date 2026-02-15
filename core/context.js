/**
 * Context gathering module.
 *
 * Ports the Python ContextManager into TypeScript with sub-context support.
 */
/** Default context manager settings */
const DEFAULT_MAX_CONTEXT_LENGTH = 128_000;
const DEFAULT_COMPACT_THRESHOLD = 0.85;
const DEFAULT_KEEP_LAST_N = 10;
/** Rough token estimation: ~4 chars per token */
function estimateTokens(text) {
    return Math.ceil(text.length / 4);
}
/**
 * Manages conversation context with auto-compaction.
 *
 * Ports the Python ContextManager class with sub-context hierarchy
 * for sub-agent orchestration.
 */
export class ContextManager {
    maxContextLength;
    compactThreshold;
    autoCompact;
    keepLastN;
    contextId;
    parentContext;
    messages = [];
    systemMessage = null;
    totalPromptTokens = 0;
    totalCompletionTokens = 0;
    estimatedContextTokens = 0;
    subContexts = new Map();
    constructor(maxContextLength = DEFAULT_MAX_CONTEXT_LENGTH, compactThreshold = DEFAULT_COMPACT_THRESHOLD, autoCompact = true, keepLastN = DEFAULT_KEEP_LAST_N, contextId, parentContext) {
        this.maxContextLength = maxContextLength;
        this.compactThreshold = compactThreshold;
        this.autoCompact = autoCompact;
        this.keepLastN = keepLastN;
        this.contextId = contextId;
        this.parentContext = parentContext;
    }
    /** Set or update the system message */
    setSystemMessage(prompt) {
        this.systemMessage = prompt;
        this.estimatedContextTokens = this.estimateCurrentTokens();
    }
    /** Add a message to the conversation history */
    addMessage(role, content, options) {
        const message = {
            role,
            content,
            ...(options?.toolCalls ? { tool_calls: options.toolCalls } : {}),
            ...(options?.toolCallId ? { tool_call_id: options.toolCallId } : {}),
        };
        this.messages.push(message);
        this.estimatedContextTokens = this.estimateCurrentTokens();
        if (this.autoCompact && this.shouldCompact()) {
            this.compact();
        }
    }
    /** Check if context compaction is needed */
    shouldCompact() {
        const usage = this.getContextUsage();
        return usage.percent >= this.compactThreshold * 100;
    }
    /** Compact the conversation by truncation (fallback). */
    compact() {
        if (this.messages.length <= this.keepLastN)
            return;
        const oldMessages = this.messages.slice(0, -this.keepLastN);
        const recentMessages = this.messages.slice(-this.keepLastN);
        // Create a summary of old messages
        const summary = oldMessages
            .map((m) => `[${m.role}]: ${m.content.slice(0, 200)}`)
            .join("\n");
        const compactedMessage = {
            role: "system",
            content: `[Context compacted - ${oldMessages.length} messages summarized]\n${summary}`,
        };
        this.messages = [compactedMessage, ...recentMessages];
        this.estimatedContextTokens = this.estimateCurrentTokens();
    }
    /**
     * Smart compaction: use LLM to summarize older messages.
     *
     * Falls back to truncation-based compact() if the LLM call fails.
     *
     * @param orchestrator - ModelOrchestrator for LLM calls
     * @param provider - Provider to use for summarization
     */
    async smartCompact(orchestrator, provider) {
        if (this.messages.length <= this.keepLastN)
            return;
        const oldMessages = this.messages.slice(0, -this.keepLastN);
        const recentMessages = this.messages.slice(-this.keepLastN);
        const conversationText = oldMessages
            .map((m) => `[${m.role}]: ${m.content.slice(0, 500)}`)
            .join("\n");
        try {
            const response = await orchestrator.complete(provider, [
                {
                    role: "system",
                    content: "You are a conversation summarizer. Produce a concise summary that preserves key decisions, code changes, file paths, and technical context. Return only the summary text, no preamble.",
                },
                {
                    role: "user",
                    content: `Summarize this conversation (${oldMessages.length} messages) into a concise context block:\n\n${conversationText}`,
                },
            ]);
            const summaryMessage = {
                role: "system",
                content: `[Smart compaction - ${oldMessages.length} messages summarized by LLM]\n${response.content}`,
            };
            this.messages = [summaryMessage, ...recentMessages];
            this.estimatedContextTokens = this.estimateCurrentTokens();
        }
        catch {
            // LLM summarization failed, fall back to truncation
            this.compact();
        }
    }
    /** Get the last N messages for context-aware operations */
    getRecentMessages(n = 5) {
        return this.messages.slice(-n);
    }
    /** Get messages formatted for API calls */
    getMessagesForApi() {
        const result = [];
        if (this.systemMessage) {
            result.push({ role: "system", content: this.systemMessage });
        }
        result.push(...this.messages);
        return result;
    }
    /** Get context window usage statistics */
    getContextUsage() {
        const used = this.estimatedContextTokens;
        return {
            used,
            max: this.maxContextLength,
            percent: Math.round((used / this.maxContextLength) * 100),
        };
    }
    /** Update token metrics from a provider response */
    updateMetrics(promptTokens, completionTokens) {
        this.totalPromptTokens += promptTokens;
        this.totalCompletionTokens += completionTokens;
    }
    /** Create a sub-context for sub-agent orchestration */
    createSubContext(contextId, systemMessage) {
        const subCtx = new ContextManager(this.maxContextLength, this.compactThreshold, this.autoCompact, this.keepLastN, contextId, this);
        if (systemMessage) {
            subCtx.setSystemMessage(systemMessage);
        }
        this.subContexts.set(contextId, subCtx);
        return subCtx;
    }
    /** Get a sub-context by ID */
    getSubContext(contextId) {
        return this.subContexts.get(contextId);
    }
    /** Get the total number of messages */
    get messageCount() {
        return this.messages.length;
    }
    /** Get total prompt tokens consumed */
    get promptTokens() {
        return this.totalPromptTokens;
    }
    /** Get total completion tokens consumed */
    get completionTokens() {
        return this.totalCompletionTokens;
    }
    /** Serialize context to JSON for persistence */
    toJSON() {
        return {
            contextId: this.contextId,
            systemMessage: this.systemMessage,
            messages: this.messages,
            totalPromptTokens: this.totalPromptTokens,
            totalCompletionTokens: this.totalCompletionTokens,
            maxContextLength: this.maxContextLength,
            subContexts: Object.fromEntries([...this.subContexts.entries()].map(([k, v]) => [k, v.toJSON()])),
        };
    }
    /** Restore context from serialized JSON */
    static fromJSON(data) {
        const ctx = new ContextManager(data.maxContextLength, undefined, undefined, undefined, data.contextId);
        if (data.systemMessage) {
            ctx.setSystemMessage(data.systemMessage);
        }
        const messages = data.messages;
        if (messages) {
            for (const msg of messages) {
                ctx.messages.push(msg);
            }
        }
        ctx.totalPromptTokens = data.totalPromptTokens ?? 0;
        ctx.totalCompletionTokens = data.totalCompletionTokens ?? 0;
        ctx.estimatedContextTokens = ctx.estimateCurrentTokens();
        return ctx;
    }
    /** Estimate current token usage */
    estimateCurrentTokens() {
        let total = 0;
        if (this.systemMessage) {
            total += estimateTokens(this.systemMessage);
        }
        for (const msg of this.messages) {
            total += estimateTokens(msg.content);
        }
        return total;
    }
}
//# sourceMappingURL=context.js.map