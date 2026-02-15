/**
 * Main agent with event-driven progress reporting.
 *
 * Ports the Python agent logic into TypeScript with EventEmitter
 * for themed progress indicators, intent classification, token
 * counting, session persistence, and hook execution.
 */
import { EventEmitter } from "node:events";
import { Provider } from "../types/message.js";
import { BUILT_IN_TOOLS } from "../types/agent.js";
import { OperationPhase } from "../types/theme.js";
import { ContextManager } from "./context.js";
import { ModelOrchestrator } from "./models.js";
import { executeTool } from "./tools.js";
import { IntentClassifier } from "./intent.js";
import { TokenCounter } from "./tokens.js";
import { HookRunner } from "./hooks.js";
import { ChainController } from "./chain.js";
/** Generate a UUID-like session ID */
function generateSessionId() {
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
    context;
    orchestrator;
    intentClassifier;
    tokenCounter;
    hookRunner;
    provider;
    model;
    sessionId;
    startTime;
    running = false;
    _messageCount = 0;
    constructor(options) {
        super();
        this.sessionId = generateSessionId();
        this.startTime = new Date();
        // Resolve provider
        this.provider = (Object.values(Provider).find((p) => p === options.provider) ??
            Provider.OLLAMA);
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
        this.context.setSystemMessage(options.systemPrompt ?? this.buildDefaultSystemPrompt());
    }
    /** Start the agent session */
    async start() {
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
    async executeTask(userInput) {
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
                intent,
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
        const chunks = [];
        const streamStart = Date.now();
        try {
            for await (const chunk of this.orchestrator.stream(this.provider, this.context.getMessagesForApi())) {
                chunks.push(chunk);
                this.emit("stream", chunk);
            }
        }
        catch (err) {
            this.emit("error", {
                error: err instanceof Error ? err : new Error(String(err)),
            });
            return "";
        }
        const streamDuration = Date.now() - streamStart;
        const response = chunks.join("");
        this.context.addMessage("assistant", response);
        // Update token counter with estimated usage
        const estimatedPromptTokens = Math.ceil(this.context
            .getMessagesForApi()
            .reduce((sum, m) => sum + m.content.length, 0) / 4);
        const estimatedCompletionTokens = Math.ceil(response.length / 4);
        this.tokenCounter.update({
            promptTokens: estimatedPromptTokens,
            completionTokens: estimatedCompletionTokens,
            totalTokens: estimatedPromptTokens + estimatedCompletionTokens,
        }, streamDuration);
        // Sync context usage into token counter
        const contextUsage = this.context.getContextUsage();
        this.tokenCounter.setContext(contextUsage.used, contextUsage.max);
        // Phase 4: Complete
        this.emit("progress", {
            phase: OperationPhase.COMPLETE,
            details: `Response ready ${this.tokenCounter.formatDisplay()}`,
        });
        this.emit("success", { message: "زبطت! Response is ready" });
        return response;
    }
    /** Send a message and get a response (non-streaming) */
    async send(message) {
        this._messageCount++;
        this.context.addMessage("user", message);
        const response = await this.orchestrator.complete(this.provider, this.context.getMessagesForApi());
        this.context.addMessage("assistant", response.content);
        if (response.usage) {
            this.context.updateMetrics(response.usage.promptTokens, response.usage.completionTokens);
            this.tokenCounter.update(response.usage);
        }
        return response;
    }
    /** Execute a tool by name */
    async runTool(toolName, args) {
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
    async end() {
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
    getStatus() {
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
    compact() {
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
    getContext() {
        return this.context;
    }
    /** Get the model orchestrator for sub-agent creation */
    getOrchestrator() {
        return this.orchestrator;
    }
    /** Get the token counter for display */
    getTokenCounter() {
        return this.tokenCounter;
    }
    /** Classify intent for a prompt without executing */
    classifyIntent(prompt) {
        return this.intentClassifier.classify(prompt);
    }
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
    async executeWithTools(userInput, maxRounds = 10) {
        if (!this.running) {
            await this.start();
        }
        this._messageCount++;
        // Phase 1: Analyzing (with intent classification)
        this.emit("progress", {
            phase: OperationPhase.ANALYZING,
            details: "Reading your request...",
        });
        const intent = this.intentClassifier.classify(userInput);
        this.emit("intent", intent);
        this.context.addMessage("user", userInput);
        // Fire UserPromptSubmit hook
        if (this.hookRunner.isEnabled()) {
            await this.hookRunner.runHook("UserPromptSubmit", {
                session_id: this.sessionId,
                message: userInput,
                intent,
            });
        }
        // Phase 2: Planning
        this.emit("progress", {
            phase: OperationPhase.PLANNING,
            details: `Intent: ${intent.agentType} (${(intent.confidence * 100).toFixed(0)}%)`,
        });
        // Phase 3: Implementing with tools
        this.emit("progress", {
            phase: OperationPhase.IMPLEMENTING,
            details: "Generating response...",
        });
        const accumulatedContent = [];
        let lastMetrics;
        for (let round = 0; round < maxRounds; round++) {
            const response = await this.orchestrator.complete(this.provider, this.context.getMessagesForApi(), this.getToolDefinitions());
            if (response.usage) {
                lastMetrics = {
                    promptTokens: response.usage.promptTokens,
                    completionTokens: response.usage.completionTokens,
                };
            }
            // No tool calls — return the final text
            if (!response.toolCalls || response.toolCalls.length === 0) {
                // Emit stream so the UI displays the response
                if (response.content) {
                    this.emit("stream", response.content);
                }
                if (accumulatedContent.length > 0) {
                    accumulatedContent.push(response.content);
                    const fullResponse = accumulatedContent.join("\n");
                    this.context.addMessage("assistant", fullResponse);
                    this.finalizeResponse(fullResponse, lastMetrics);
                    return fullResponse;
                }
                this.context.addMessage("assistant", response.content);
                this.finalizeResponse(response.content, lastMetrics);
                return response.content;
            }
            // Model wants to call tools — execute them
            if (response.content) {
                accumulatedContent.push(response.content);
                this.emit("stream", response.content);
            }
            // Record the assistant message with tool calls
            this.context.addMessage("assistant", response.content || "", {
                toolCalls: response.toolCalls,
            });
            // Execute each tool call and append results
            for (const tc of response.toolCalls) {
                const toolName = tc.function.name;
                let args;
                try {
                    args = JSON.parse(tc.function.arguments);
                }
                catch {
                    args = {};
                }
                this.emit("progress", {
                    phase: OperationPhase.TESTING,
                    details: `Executing tool: ${toolName}`,
                });
                const result = await this.runTool(toolName, args);
                const resultStr = JSON.stringify({ success: result.success, output: result.output, error: result.error }).slice(0, 3000);
                this.context.addMessage("tool", resultStr, { toolCallId: tc.id });
            }
        }
        // Max rounds reached — return what we have
        const fallback = accumulatedContent.length > 0
            ? accumulatedContent.join("\n")
            : "[max tool-call rounds reached]";
        this.context.addMessage("assistant", fallback);
        this.finalizeResponse(fallback, lastMetrics);
        return fallback;
    }
    /** Finalize a response by updating token counter and emitting events */
    finalizeResponse(response, metrics) {
        if (metrics) {
            this.tokenCounter.update({
                promptTokens: metrics.promptTokens,
                completionTokens: metrics.completionTokens,
                totalTokens: metrics.promptTokens + metrics.completionTokens,
            });
            this.context.updateMetrics(metrics.promptTokens, metrics.completionTokens);
        }
        const contextUsage = this.context.getContextUsage();
        this.tokenCounter.setContext(contextUsage.used, contextUsage.max);
        this.emit("progress", {
            phase: OperationPhase.COMPLETE,
            details: `Response ready ${this.tokenCounter.formatDisplay()}`,
        });
        this.emit("success", { message: "Response is ready" });
    }
    /** Get the tool definitions for API calls */
    getToolDefinitions() {
        return BUILT_IN_TOOLS;
    }
    /**
     * Execute a request using the chained sub-agent orchestration.
     *
     * Runs Wave 0 (Ingest) then Waves 1-4 with parallel fan-out,
     * merging outputs into SharedState between each wave.
     *
     * @param chainConfig - Optional per-wave agent configs
     * @returns The chain result with final answer and audit trail
     */
    async executeWithChain(userInput, chainConfig) {
        if (!this.running) {
            await this.start();
        }
        this._messageCount++;
        // Classify intent
        const intent = this.intentClassifier.classify(userInput);
        this.emit("intent", intent);
        // Fire UserPromptSubmit hook
        if (this.hookRunner.isEnabled()) {
            await this.hookRunner.runHook("UserPromptSubmit", {
                session_id: this.sessionId,
                message: userInput,
                intent,
            });
        }
        const chain = new ChainController({
            orchestrator: this.orchestrator,
            context: this.context,
            provider: this.provider,
            waves: chainConfig?.waves,
            agentConfigs: chainConfig?.agentConfigs,
        });
        // Forward chain events to agent listeners
        chain.on("progress", (data) => this.emit("progress", data));
        chain.on("wave:start", (data) => {
            this.emit("chain:wave", { ...data, status: "started" });
            if (this.hookRunner.isEnabled()) {
                this.hookRunner.runHook("SubagentStart", {
                    session_id: this.sessionId,
                    wave: data.wave,
                    name: data.name,
                    agents: data.agents,
                }).catch(() => { });
            }
        });
        chain.on("wave:complete", (data) => {
            this.emit("chain:wave", { ...data, status: "completed" });
            if (this.hookRunner.isEnabled()) {
                this.hookRunner.runHook("SubagentStop", {
                    session_id: this.sessionId,
                    wave: data.wave,
                    name: data.name,
                }).catch(() => { });
            }
        });
        chain.on("merge:complete", (data) => this.emit("chain:merge", data));
        chain.on("contract:violation", (data) => this.emit("chain:contract", data));
        const result = await chain.run(userInput);
        // Emit the final answer as stream for UI display
        if (result.finalAnswer) {
            this.emit("stream", result.finalAnswer);
        }
        // Store in context
        this.context.addMessage("user", userInput);
        this.context.addMessage("assistant", result.finalAnswer);
        this.emit("progress", {
            phase: OperationPhase.COMPLETE,
            details: `Chain complete ${this.tokenCounter.formatDisplay()}`,
        });
        this.emit("success", { message: "Chain orchestration complete" });
        return result;
    }
    /** Build the default system prompt */
    buildDefaultSystemPrompt() {
        const toolList = BUILT_IN_TOOLS
            .map((t) => `- ${t.name}: ${t.description}`)
            .join("\n");
        return [
            "You are Qarin (قرين), an AI coding assistant.",
            "You help developers write, debug, test, and improve code.",
            "Be concise, accurate, and helpful.",
            "When writing code, follow the project's existing conventions.",
            "",
            "You have access to the following tools:",
            toolList,
            "",
            "When a user asks you to perform an action (reading files, editing code,",
            "running shell commands, searching files, or fetching URLs), use the",
            "appropriate tool call to execute the action.",
        ].join("\n");
    }
}
//# sourceMappingURL=agent.js.map