/**
 * Main agent with event-driven progress reporting.
 *
 * Ports the Python agent logic into TypeScript with EventEmitter
 * for themed progress indicators.
 */

import { EventEmitter } from "node:events";

import type { Message, ModelResponse } from "../types/message.js";
import { Provider } from "../types/message.js";
import type { CLIOptions, SessionConfig, SessionStatus, ToolResult } from "../types/agent.js";
import { BUILT_IN_TOOLS } from "../types/agent.js";
import { OperationPhase } from "../types/theme.js";
import { ContextManager } from "./context.js";
import { ModelOrchestrator } from "./models.js";
import { executeTool } from "./tools.js";

/** Events emitted by the agent */
export interface AgentEvents {
  progress: (event: { phase: OperationPhase; details?: string }) => void;
  stream: (chunk: string) => void;
  toolUse: (event: { tool: string; args: Record<string, unknown> }) => void;
  toolResult: (event: { tool: string; result: ToolResult }) => void;
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
 * Usage:
 * ```ts
 * const agent = new QarinAgent({ model: 'claude-sonnet-4', provider: 'anthropic', theme: 'shisha' });
 * agent.on('progress', ({ phase, details }) => console.log(phase, details));
 * agent.on('stream', (chunk) => process.stdout.write(chunk));
 * await agent.start();
 * await agent.executeTask('Fix the bug in auth.ts');
 * await agent.end();
 * ```
 */
export class QarinAgent extends EventEmitter {
  private context: ContextManager;
  private orchestrator: ModelOrchestrator;
  private provider: Provider;
  private model: string;
  private sessionId: string;
  private startTime: Date;
  private running = false;

  constructor(options: CLIOptions) {
    super();
    this.sessionId = generateSessionId();
    this.startTime = new Date();

    // Resolve provider
    this.provider = (Object.values(Provider).find((p) => p === options.provider) ??
      Provider.OLLAMA) as Provider;
    this.model = options.model;

    // Initialize context manager
    this.context = new ContextManager();

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

    // Phase 1: Analyzing
    this.emit("progress", {
      phase: OperationPhase.ANALYZING,
      details: "Reading your request...",
    });

    this.context.addMessage("user", userInput);

    // Phase 2: Planning
    this.emit("progress", {
      phase: OperationPhase.PLANNING,
      details: "Preparing response...",
    });

    // Phase 3: Implementing (streaming)
    this.emit("progress", {
      phase: OperationPhase.IMPLEMENTING,
      details: "Generating response...",
    });

    const chunks: string[] = [];
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

    const response = chunks.join("");
    this.context.addMessage("assistant", response);

    // Phase 4: Complete
    this.emit("progress", {
      phase: OperationPhase.COMPLETE,
      details: "Response ready",
    });

    this.emit("success", { message: "زبطت! Response is ready" });
    return response;
  }

  /** Send a message and get a response (non-streaming) */
  async send(message: string): Promise<ModelResponse> {
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
    }

    return response;
  }

  /** Execute a tool by name */
  async runTool(toolName: string, args: Record<string, unknown>): Promise<ToolResult> {
    this.emit("toolUse", { tool: toolName, args });
    const result = await executeTool(toolName, args);
    this.emit("toolResult", { tool: toolName, result });
    return result;
  }

  /** End the session */
  async end(): Promise<SessionStatus> {
    this.running = false;
    const status = this.getStatus();
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
      messageCount: this.context.messageCount,
      contextUsage,
      tokenUsage: {
        promptTokens: this.context.promptTokens,
        completionTokens: this.context.completionTokens,
        totalTokens: this.context.promptTokens + this.context.completionTokens,
      },
      startTime: this.startTime.toISOString(),
      duration: (now.getTime() - this.startTime.getTime()) / 1000,
    };
  }

  /** Compact the context window */
  compact(): void {
    this.context.compact();
    this.emit("progress", {
      phase: OperationPhase.REVIEWING,
      details: "Context compacted",
    });
  }

  /** Get the context manager for sub-agent creation */
  getContext(): ContextManager {
    return this.context;
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
