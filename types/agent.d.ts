/**
 * Agent and session types for the qarin-cli core.
 */
import type { Provider, TokenUsage, ToolDefinition } from "./message.js";
import type { ThemeName } from "./theme.js";
/** CLI options from commander */
export interface CLIOptions {
    model: string;
    provider: string;
    theme: ThemeName;
    print?: boolean;
    resume?: boolean;
    systemPrompt?: string;
    outputFormat?: "text" | "json" | "markdown";
}
/** Session configuration */
export interface SessionConfig {
    sessionId: string;
    model: string;
    provider: Provider;
    maxContextLength: number;
    compactThreshold: number;
    autoCompact: boolean;
    keepLastN: number;
}
/** Session status snapshot */
export interface SessionStatus {
    sessionId: string;
    model: string;
    provider: Provider;
    messageCount: number;
    contextUsage: ContextUsage;
    tokenUsage: TokenUsage;
    startTime: string;
    duration: number;
}
/** Context window usage */
export interface ContextUsage {
    used: number;
    max: number;
    percent: number;
}
/** Agent type classification */
export type AgentType = "code" | "review" | "test" | "debug" | "plan" | "docs" | "research" | "orchestrator";
/** Intent classification result */
export interface IntentResult {
    agentType: AgentType;
    confidence: number;
    matchedPatterns: string[];
    explanation?: string;
}
/** Agent model assignment from settings */
export interface AgentModelConfig {
    provider: Provider;
    model: string;
}
/** Tool execution result */
export interface ToolResult {
    success: boolean;
    output: string;
    error?: string;
}
/** Hook execution result */
export interface HookResult {
    success: boolean;
    stdout: string;
    stderr: string;
    returnCode: number;
    parsed?: Record<string, unknown>;
    error?: string;
}
/** Sub-agent wave definition */
export interface Wave {
    waveNumber: number;
    agents: string[];
    results: Record<string, unknown>[];
    status: "pending" | "running" | "completed" | "failed";
    timestamp?: string;
}
/** Shared state for sub-agent orchestration */
export interface SharedState {
    userInput: string;
    constraints: string[];
    analysisResults: Record<string, unknown>;
    plan: Record<string, unknown>;
    executionOutputs: Record<string, unknown>[];
    status: string;
}
/** Memory entry for persistent knowledge */
export interface MemoryEntry {
    key: string;
    content: string;
    category: "fact" | "preference" | "context" | "learned";
    importance: number;
    tokenCost: number;
    createdAt: string;
    lastAccessed: string;
    accessCount: number;
}
/** Agent-to-agent message */
export interface AgentMessage {
    sender: string;
    recipient: string;
    content: string;
    messageType: string;
    timestamp: string;
    tokenCost: number;
}
/** Available built-in tools */
export declare const BUILT_IN_TOOLS: ToolDefinition[];
//# sourceMappingURL=agent.d.ts.map