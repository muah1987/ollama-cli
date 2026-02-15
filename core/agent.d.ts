/**
 * Main agent with event-driven progress reporting.
 *
 * Ports the Python agent logic into TypeScript with EventEmitter
 * for themed progress indicators, intent classification, token
 * counting, session persistence, and hook execution.
 */
import { EventEmitter } from "node:events";
import type { ModelResponse } from "../types/message.js";
import type { CLIOptions, IntentResult, SessionStatus, ToolResult } from "../types/agent.js";
import type { ToolDefinition } from "../types/message.js";
import { OperationPhase } from "../types/theme.js";
import { ContextManager } from "./context.js";
import { ModelOrchestrator } from "./models.js";
import { TokenCounter } from "./tokens.js";
/** Events emitted by the agent */
export interface AgentEvents {
    progress: (event: {
        phase: OperationPhase;
        details?: string;
    }) => void;
    stream: (chunk: string) => void;
    toolUse: (event: {
        tool: string;
        args: Record<string, unknown>;
    }) => void;
    toolResult: (event: {
        tool: string;
        result: ToolResult;
    }) => void;
    intent: (event: IntentResult) => void;
    success: (event: {
        message: string;
    }) => void;
    error: (event: {
        error: Error;
    }) => void;
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
export declare class QarinAgent extends EventEmitter {
    private context;
    private orchestrator;
    private intentClassifier;
    private tokenCounter;
    private hookRunner;
    private provider;
    private model;
    private sessionId;
    private startTime;
    private running;
    private _messageCount;
    constructor(options: CLIOptions);
    /** Start the agent session */
    start(): Promise<void>;
    /** Execute a task with themed progress phases */
    executeTask(userInput: string): Promise<string>;
    /** Send a message and get a response (non-streaming) */
    send(message: string): Promise<ModelResponse>;
    /** Execute a tool by name */
    runTool(toolName: string, args: Record<string, unknown>): Promise<ToolResult>;
    /** End the session */
    end(): Promise<SessionStatus>;
    /** Get current session status */
    getStatus(): SessionStatus;
    /** Compact the context window */
    compact(): void;
    /** Get the context manager for sub-agent creation */
    getContext(): ContextManager;
    /** Get the model orchestrator for sub-agent creation */
    getOrchestrator(): ModelOrchestrator;
    /** Get the token counter for display */
    getTokenCounter(): TokenCounter;
    /** Classify intent for a prompt without executing */
    classifyIntent(prompt: string): IntentResult;
    /**
     * Execute a request with an agentic tool-call loop.
     *
     * When the model responds with tool calls, this method:
     * 1. Executes each tool via runTool()
     * 2. Appends tool results to the conversation
     * 3. Re-queries the model until it produces a final text response
     *
     * Matches the Python Session._route_with_tools() pattern.
     *
     * @param maxRounds - Maximum tool-call rounds to prevent runaway loops
     * @returns The final text response from the model
     */
    executeWithTools(userInput: string, maxRounds?: number): Promise<string>;
    /** Finalize a response by updating token counter and emitting events */
    private finalizeResponse;
    /** Get the tool definitions for API calls */
    getToolDefinitions(): ToolDefinition[];
    /** Build the default system prompt */
    private buildDefaultSystemPrompt;
}
//# sourceMappingURL=agent.d.ts.map