/**
 * Multi-provider model abstraction layer.
 *
 * Ports the Python providers/ directory into a single unified module
 * with async generator streaming support.
 */
import type { Message, ModelResponse, ProviderConfig, TokenUsage } from "../types/message.js";
import { Provider } from "../types/message.js";
/** Interface that all LLM providers must implement */
export interface LLMProvider {
    readonly provider: Provider;
    readonly model: string;
    complete(messages: Message[]): AsyncGenerator<string>;
    completeSync(messages: Message[]): Promise<ModelResponse>;
}
/**
 * Anthropic (Claude) provider implementation.
 */
export declare class AnthropicProvider implements LLMProvider {
    readonly model: string;
    private readonly apiKey;
    private readonly baseUrl;
    private readonly maxTokens;
    readonly provider = Provider.ANTHROPIC;
    constructor(model?: string, apiKey?: string, baseUrl?: string, maxTokens?: number);
    complete(messages: Message[]): AsyncGenerator<string>;
    completeSync(messages: Message[]): Promise<ModelResponse>;
}
/**
 * OpenAI (GPT) provider implementation.
 */
export declare class OpenAIProvider implements LLMProvider {
    readonly model: string;
    private readonly apiKey;
    private readonly maxTokens;
    readonly provider = Provider.OPENAI;
    constructor(model?: string, apiKey?: string, maxTokens?: number);
    complete(messages: Message[]): AsyncGenerator<string>;
    completeSync(messages: Message[]): Promise<ModelResponse>;
}
/**
 * Ollama (local) provider implementation.
 */
export declare class OllamaProvider implements LLMProvider {
    readonly model: string;
    private readonly host;
    readonly provider = Provider.OLLAMA;
    constructor(model?: string, host?: string);
    complete(messages: Message[]): AsyncGenerator<string>;
    completeSync(messages: Message[]): Promise<ModelResponse>;
}
/**
 * Model orchestrator that manages multiple providers and handles fallback.
 *
 * Ports the Python ProviderRouter class.
 */
export declare class ModelOrchestrator {
    private providers;
    constructor(configs?: ProviderConfig[]);
    /** Register a provider from config */
    registerProvider(config: ProviderConfig): void;
    /** Stream responses from a provider with fallback */
    stream(provider: Provider, messages: Message[]): AsyncGenerator<string>;
    /** Get a synchronous response from a provider */
    complete(provider: Provider, messages: Message[]): Promise<ModelResponse>;
    /** Try providers in fallback order until one succeeds */
    streamWithFallback(messages: Message[]): AsyncGenerator<string>;
    /** Calculate cost for token usage */
    static calculateCost(provider: Provider, usage: TokenUsage): number;
    /** Get registered provider names */
    getRegisteredProviders(): Provider[];
}
//# sourceMappingURL=models.d.ts.map