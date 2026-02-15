/**
 * Main agent with event-driven progress reporting.
 *
 * Ports the Python agent logic into TypeScript with EventEmitter
 * for themed progress indicators, intent classification, token
 * counting, session persistence, and hook execution.
 */

import { EventEmitter } from "node:events";

import type { Message, ModelResponse } from "../types/message.js";
import { Provider } from "../types/message.js";
import type { CLIOptions, IntentResult, SessionStatus, ToolResult } from "../types/agent.js";
import { OperationPhase } from "../types/theme.js";
import { ContextManager } from "./context.js";
import { ModelOrchestrator } from "./models.js";
import { executeTool } from "./tools.js";
import { IntentClassifier } from "./intent.js";
import { TokenCounter } from "./tokens.js";
import { HookRunner } from "./hooks.js";

/** Events emitted by the agent */
export interface AgentEvents {
  progress: (event: { phase: OperationPhase; details?: string }) => void;
  stream: (chunk: string) => void;
  toolUse: (event: { tool: string; args: Record<string, unknown> }) => void;
  toolResult: (event: { tool: string; result: ToolResult }) => void;
  intent: (event: IntentResult) => void;
  success: (event: { message: string }) => void;
  error: (event: { error: Error }) => void;
}

/** Generate a UUID-like session ID */
function generateSessionId(): string {
  return crypto.randomUUID();
}

/**
 * Core agent that orchestrates LLM interactions with themed progress.
 *
 * Integrates:
 * - Multi-provider LLM streaming via ModelOrchestrator
 * - Intent classification via IntentClassifier (Tier 1 pattern matching)
 * - Real-time token counting with cost estimation via TokenCounter
 * - Lifecycle hooks via HookRunner
 * - Context auto-compaction via ContextManager
 *
 * Usage:
 * ```ts
 * const agent = new QarinAgent({ model: 'claude-sonnet-4', provider: 'anthropic', theme: 'shisha' });
 * agent.on('progress', ({ phase, details }) => console.log(phase, details));
 * agent.on('stream', (chunk) => process.stdout.write(chunk));
 * agent.on('intent', (intent) => console.log('Intent:', intent.agentType));
 * await agent.start();
 * await agent.executeTask('Fix the bug in auth.ts');
 * await agent.end();
 * ```
 */
export class QarinAgent extends EventEmitter {
  private context: ContextManager;
  private orchestrator: ModelOrchestrator;
  private intentClassifier: IntentClassifier;
  private tokenCounter: TokenCounter;
  private hookRunner: HookRunner;
  private provider: Provider;
  private model: string;
  private sessionId: string;
  private startTime: Date;
  private running = false;
  private _messageCount = 0;

  constructor(options: CLIOptions) {
    super();
    this.sessionId = generateSessionId();
    this.startTime = new Date();

    // Resolve provider
    this.provider = (Object.values(Provider).find((p) => p === options.provider) ??
      Provider.OLLAMA) as Provider;
    this.model = options.model;

    // Initialize core modules
    this.context = new ContextManager();
    this.intentClassifier = new IntentClassifier();
    this.tokenCounter = new TokenCounter(this.provider, 128_000);
    this.hookRunner = new HookRunner();

    // Initialize model orchestrator with the selected provider
    this.orchestrator = new ModelOrchestrator();
    this.orchestrator.registerProvider({
      provider: this.provider,
      model: this.model,
    });

    // Set system prompt
    this.context.setSystemMessage(
      options.systemPrompt ?? this.buildDefaultSystemPrompt(),
    );
  }

  /** Start the agent session */
  async start(): Promise<void> {
    this.running = true;
    this.startTime = new Date();

    // Load hook configuration
    await this.hookRunner.load();

    // Fire SessionStart hook
    if (this.hookRunner.isEnabled()) {
      await this.hookRunner.runHook("SessionStart", {
        session_id: this.sessionId,
        model: this.model,
        provider: this.provider,
      });
    }

    this.emit("progress", {
      phase: OperationPhase.ANALYZING,
      details: "Session started",
    });
  }

  /** Execute a task with themed progress phases */
  async executeTask(userInput: string): Promise<string> {
    if (!this.running) {
      await this.start();
    }

    this._messageCount++;

    // Phase 1: Analyzing (with intent classification)
    this.emit("progress", {
      phase: OperationPhase.ANALYZING,
      details: "Reading your request...",
    });

    // Classify intent
    const intent = this.intentClassifier.classify(userInput);
    this.emit("intent", intent);

    this.context.addMessage("user", userInput);

    // Fire UserPromptSubmit hook
    if (this.hookRunner.isEnabled()) {
      await this.hookRunner.runHook("UserPromptSubmit", {
        session_id: this.sessionId,
        message: userInput,
        intent: intent.agentType,
        confidence: intent.confidence,
      });
    }

    // Phase 2: Planning
    this.emit("progress", {
      phase: OperationPhase.PLANNING,
      details: `Intent: ${intent.agentType} (${(intent.confidence * 100).toFixed(0)}%)`,
    });

    // Phase 3: Implementing (streaming)
    this.emit("progress", {
      phase: OperationPhase.IMPLEMENTING,
      details: "Generating response...",
    });

    const chunks: string[] = [];
    const streamStart = Date.now();
    try {
      for await (const chunk of this.orchestrator.stream(
        this.provider,
        this.context.getMessagesForApi(),
      )) {
        chunks.push(chunk);
        this.emit("stream", chunk);
      }
    } catch (err) {
      this.emit("error", {
        error: err instanceof Error ? err : new Error(String(err)),
      });
      return "";
    }
    const streamDuration = Date.now() - streamStart;

    const response = chunks.join("");
    this.context.addMessage("assistant", response);

    // Update token counter with estimated usage
    const estimatedPromptTokens = Math.ceil(
      this.context
        .getMessagesForApi()
        .reduce((sum, m) => sum + m.content.length, 0) / 4,
    );
    const estimatedCompletionTokens = Math.ceil(response.length / 4);
    this.tokenCounter.update(
      {
        promptTokens: estimatedPromptTokens,
        completionTokens: estimatedCompletionTokens,
        totalTokens: estimatedPromptTokens + estimatedCompletionTokens,
      },
      streamDuration,
    );

    // Sync context usage into token counter
    const contextUsage = this.context.getContextUsage();
    this.tokenCounter.setContext(contextUsage.used, contextUsage.max);

    // Phase 4: Complete
    this.emit("progress", {
      phase: OperationPhase.COMPLETE,
      details: `Response ready ${this.tokenCounter.formatDisplay()}`,
    });

    this.emit("success", { message: "Response is ready" });
    return response;
  }

  /** Send a message and get a response (non-streaming) */
  async send(message: string): Promise<ModelResponse> {
    this._messageCount++;
    this.context.addMessage("user", message);

    const response = await this.orchestrator.complete(
      this.provider,
      this.context.getMessagesForApi(),
    );

    this.context.addMessage("assistant", response.content);

    if (response.usage) {
      this.context.updateMetrics(
        response.usage.promptTokens,
        response.usage.completionTokens,
      );
      this.tokenCounter.update(response.usage);
    }

    return response;
  }

  /** Execute a tool by name */
  async runTool(toolName: string, args: Record<string, unknown>): Promise<ToolResult> {
    // Fire PreToolUse hook
    if (this.hookRunner.isEnabled()) {
      const hookResults = await this.hookRunner.runHook("PreToolUse", {
        session_id: this.sessionId,
        tool_name: toolName,
        arguments: args,
      });

      // Check for permission denial
      for (const hr of hookResults) {
        if (hr.parsed?.permissionDecision === "deny") {
          return {
            success: false,
            output: "",
            error: `Tool ${toolName} denied by hook: ${hr.parsed.additionalContext ?? "no reason given"}`,
          };
        }
      }
    }

    this.emit("toolUse", { tool: toolName, args });
    const result = await executeTool(toolName, args);
    this.emit("toolResult", { tool: toolName, result });

    // Fire PostToolUse hook
    if (this.hookRunner.isEnabled()) {
      const eventName = result.success ? "PostToolUse" : "PostToolUseFailure";
      await this.hookRunner.runHook(eventName, {
        session_id: this.sessionId,
        tool_name: toolName,
        result: { success: result.success, output: result.output.slice(0, 500) },
      });
    }

    return result;
  }

  /** End the session */
  async end(): Promise<SessionStatus> {
    this.running = false;
    const status = this.getStatus();

    // Fire SessionEnd hook
    if (this.hookRunner.isEnabled()) {
      await this.hookRunner.runHook("SessionEnd", {
        session_id: this.sessionId,
        model: this.model,
        provider: this.provider,
        messages: this._messageCount,
        tokens: this.tokenCounter.totalTokens,
        cost: this.tokenCounter.costEstimate,
      });
    }

    this.emit("progress", {
      phase: OperationPhase.COMPLETE,
      details: "Session ended",
    });
    return status;
  }

  /** Get current session status */
  getStatus(): SessionStatus {
    const now = new Date();
    const contextUsage = this.context.getContextUsage();

    return {
      sessionId: this.sessionId,
      model: this.model,
      provider: this.provider,
      messageCount: this._messageCount,
      contextUsage,
      tokenUsage: {
        promptTokens: this.tokenCounter.promptTokens,
        completionTokens: this.tokenCounter.completionTokens,
        totalTokens: this.tokenCounter.totalTokens,
      },
      startTime: this.startTime.toISOString(),
      duration: (now.getTime() - this.startTime.getTime()) / 1000,
    };
  }

  /** Compact the context window */
  compact(): void {
    this.context.compact();

    // Sync context usage after compaction
    const contextUsage = this.context.getContextUsage();
    this.tokenCounter.setContext(contextUsage.used, contextUsage.max);

    this.emit("progress", {
      phase: OperationPhase.REVIEWING,
      details: "Context compacted",
    });
  }

  /** Get the context manager for sub-agent creation */
  getContext(): ContextManager {
    return this.context;
  }

  /** Get the model orchestrator for sub-agent creation */
  getOrchestrator(): ModelOrchestrator {
    return this.orchestrator;
  }

  /** Get the token counter for display */
  getTokenCounter(): TokenCounter {
    return this.tokenCounter;
  }

  /** Classify intent for a prompt without executing */
  classifyIntent(prompt: string): IntentResult {
    return this.intentClassifier.classify(prompt);
  }

  /** Build the default system prompt */
  private buildDefaultSystemPrompt(): string {
    return [
      "You are Qarin (قرين), an AI coding assistant.",
      "You help developers write, debug, test, and improve code.",
      "You have access to file operations, shell commands, and web search.",
      "Be concise, accurate, and helpful.",
      "When writing code, follow the project's existing conventions.",
    ].join("\n");
  }
}
