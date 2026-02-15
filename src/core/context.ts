/**
 * Context gathering module.
 *
 * Ports the Python ContextManager into TypeScript with sub-context support.
 */

import type { Message } from "../types/message.js";
import type { ContextUsage } from "../types/agent.js";

/** Default context manager settings */
const DEFAULT_MAX_CONTEXT_LENGTH = 128_000;
const DEFAULT_COMPACT_THRESHOLD = 0.85;
const DEFAULT_KEEP_LAST_N = 10;

/** Rough token estimation: ~4 chars per token */
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

/**
 * Manages conversation context with auto-compaction.
 *
 * Ports the Python ContextManager class with sub-context hierarchy
 * for sub-agent orchestration.
 */
export class ContextManager {
  private messages: Message[] = [];
  private systemMessage: string | null = null;
  private totalPromptTokens = 0;
  private totalCompletionTokens = 0;
  private estimatedContextTokens = 0;
  private subContexts: Map<string, ContextManager> = new Map();

  constructor(
    private readonly maxContextLength: number = DEFAULT_MAX_CONTEXT_LENGTH,
    private readonly compactThreshold: number = DEFAULT_COMPACT_THRESHOLD,
    private readonly autoCompact: boolean = true,
    private readonly keepLastN: number = DEFAULT_KEEP_LAST_N,
    private readonly contextId?: string,
    private readonly parentContext?: ContextManager,
  ) {}

  /** Set or update the system message */
  setSystemMessage(prompt: string): void {
    this.systemMessage = prompt;
    this.estimatedContextTokens = this.estimateCurrentTokens();
  }

  /** Add a message to the conversation history */
  addMessage(
    role: Message["role"],
    content: string,
    options?: { toolCalls?: Message["tool_calls"]; toolCallId?: string },
  ): void {
    const message: Message = {
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
  shouldCompact(): boolean {
    const usage = this.getContextUsage();
    return usage.percent >= this.compactThreshold * 100;
  }

  /** Compact the conversation by summarizing older messages */
  compact(): void {
    if (this.messages.length <= this.keepLastN) return;

    const oldMessages = this.messages.slice(0, -this.keepLastN);
    const recentMessages = this.messages.slice(-this.keepLastN);

    // Create a summary of old messages
    const summary = oldMessages
      .map((m) => `[${m.role}]: ${m.content.slice(0, 200)}`)
      .join("\n");

    const compactedMessage: Message = {
      role: "system",
      content: `[Context compacted - ${oldMessages.length} messages summarized]\n${summary}`,
    };

    this.messages = [compactedMessage, ...recentMessages];
    this.estimatedContextTokens = this.estimateCurrentTokens();
  }

  /** Get messages formatted for API calls */
  getMessagesForApi(): Message[] {
    const result: Message[] = [];

    if (this.systemMessage) {
      result.push({ role: "system", content: this.systemMessage });
    }

    result.push(...this.messages);
    return result;
  }

  /** Get context window usage statistics */
  getContextUsage(): ContextUsage {
    const used = this.estimatedContextTokens;
    return {
      used,
      max: this.maxContextLength,
      percent: Math.round((used / this.maxContextLength) * 100),
    };
  }

  /** Update token metrics from a provider response */
  updateMetrics(promptTokens: number, completionTokens: number): void {
    this.totalPromptTokens += promptTokens;
    this.totalCompletionTokens += completionTokens;
  }

  /** Create a sub-context for sub-agent orchestration */
  createSubContext(contextId: string, systemMessage?: string): ContextManager {
    const subCtx = new ContextManager(
      this.maxContextLength,
      this.compactThreshold,
      this.autoCompact,
      this.keepLastN,
      contextId,
      this,
    );

    if (systemMessage) {
      subCtx.setSystemMessage(systemMessage);
    }

    this.subContexts.set(contextId, subCtx);
    return subCtx;
  }

  /** Get a sub-context by ID */
  getSubContext(contextId: string): ContextManager | undefined {
    return this.subContexts.get(contextId);
  }

  /** Get the total number of messages */
  get messageCount(): number {
    return this.messages.length;
  }

  /** Get total prompt tokens consumed */
  get promptTokens(): number {
    return this.totalPromptTokens;
  }

  /** Get total completion tokens consumed */
  get completionTokens(): number {
    return this.totalCompletionTokens;
  }

  /** Serialize context to JSON for persistence */
  toJSON(): Record<string, unknown> {
    return {
      contextId: this.contextId,
      systemMessage: this.systemMessage,
      messages: this.messages,
      totalPromptTokens: this.totalPromptTokens,
      totalCompletionTokens: this.totalCompletionTokens,
      maxContextLength: this.maxContextLength,
      subContexts: Object.fromEntries(
        [...this.subContexts.entries()].map(([k, v]) => [k, v.toJSON()]),
      ),
    };
  }

  /** Restore context from serialized JSON */
  static fromJSON(data: Record<string, unknown>): ContextManager {
    const ctx = new ContextManager(
      data.maxContextLength as number,
      undefined,
      undefined,
      undefined,
      data.contextId as string,
    );

    if (data.systemMessage) {
      ctx.setSystemMessage(data.systemMessage as string);
    }

    const messages = data.messages as Message[];
    if (messages) {
      for (const msg of messages) {
        ctx.messages.push(msg);
      }
    }

    ctx.totalPromptTokens = (data.totalPromptTokens as number) ?? 0;
    ctx.totalCompletionTokens = (data.totalCompletionTokens as number) ?? 0;
    ctx.estimatedContextTokens = ctx.estimateCurrentTokens();

    return ctx;
  }

  /** Estimate current token usage */
  private estimateCurrentTokens(): number {
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
