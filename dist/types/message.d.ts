/**
 * Message types for multi-provider LLM communication.
 */
/** Supported LLM providers */
export declare enum Provider {
    ANTHROPIC = "anthropic",
    OPENAI = "openai",
    OLLAMA = "ollama"
}
/** Role in a conversation */
export type MessageRole = "system" | "user" | "assistant" | "tool";
/** A single message in a conversation */
export interface Message {
    role: MessageRole;
    content: string;
    name?: string;
    tool_calls?: ToolCall[];
    tool_call_id?: string;
}
/** A tool call request from the model */
export interface ToolCall {
    id: string;
    type: "function";
    function: {
        name: string;
        arguments: string;
    };
}
/** Tool definition for the model */
export interface ToolDefinition {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
}
/** Token usage metrics from a provider response */
export interface TokenUsage {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
}
/** A completed response from the model */
export interface ModelResponse {
    content: string;
    toolCalls?: ToolCall[];
    usage?: TokenUsage;
    model: string;
    provider: Provider;
    finishReason?: "stop" | "tool_calls" | "length" | "error";
}
/** Provider-specific configuration */
export interface ProviderConfig {
    provider: Provider;
    model: string;
    apiKey?: string;
    baseUrl?: string;
    maxTokens?: number;
    temperature?: number;
}
/** Cost per million tokens (input/output) by provider */
export interface CostRate {
    inputPerMillion: number;
    outputPerMillion: number;
}
/** Fallback chain order for provider routing */
export declare const PROVIDER_FALLBACK_ORDER: Provider[];
//# sourceMappingURL=message.d.ts.map