/**
 * Multi-provider model abstraction layer.
 *
 * Ports the Python providers/ directory into a single unified module
 * with async generator streaming support.
 */
import { Provider, PROVIDER_FALLBACK_ORDER } from "../types/message.js";
/** Cost per million tokens by provider */
const COST_PER_MILLION = {
    [Provider.ANTHROPIC]: { input: 3.0, output: 15.0 },
    [Provider.OPENAI]: { input: 5.0, output: 15.0 },
    [Provider.OLLAMA]: { input: 0.0, output: 0.0 },
};
/**
 * Anthropic (Claude) provider implementation.
 */
export class AnthropicProvider {
    model;
    apiKey;
    baseUrl;
    maxTokens;
    provider = Provider.ANTHROPIC;
    constructor(model = "claude-sonnet-4-20250514", apiKey = process.env.ANTHROPIC_API_KEY ?? "", baseUrl = "https://api.anthropic.com", maxTokens = 4096) {
        this.model = model;
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.maxTokens = maxTokens;
    }
    async *complete(messages) {
        const { default: Anthropic } = await import("@anthropic-ai/sdk");
        const client = new Anthropic({ apiKey: this.apiKey });
        const apiMessages = messages
            .filter((m) => m.role !== "system")
            .map((m) => ({ role: m.role, content: m.content }));
        const systemMessage = messages.find((m) => m.role === "system")?.content;
        const stream = client.messages.stream({
            model: this.model,
            max_tokens: this.maxTokens,
            messages: apiMessages,
            ...(systemMessage ? { system: systemMessage } : {}),
        });
        for await (const event of stream) {
            if (event.type === "content_block_delta" &&
                "delta" in event &&
                event.delta.type === "text_delta") {
                yield event.delta.text;
            }
        }
    }
    async completeSync(messages) {
        const chunks = [];
        for await (const chunk of this.complete(messages)) {
            chunks.push(chunk);
        }
        return {
            content: chunks.join(""),
            model: this.model,
            provider: this.provider,
            finishReason: "stop",
        };
    }
}
/**
 * OpenAI (GPT) provider implementation.
 */
export class OpenAIProvider {
    model;
    apiKey;
    maxTokens;
    provider = Provider.OPENAI;
    constructor(model = "gpt-4", apiKey = process.env.OPENAI_API_KEY ?? "", maxTokens = 4096) {
        this.model = model;
        this.apiKey = apiKey;
        this.maxTokens = maxTokens;
    }
    async *complete(messages) {
        const { default: OpenAI } = await import("openai");
        const client = new OpenAI({ apiKey: this.apiKey });
        const stream = await client.chat.completions.create({
            model: this.model,
            messages: messages.map((m) => ({
                role: m.role,
                content: m.content,
            })),
            max_tokens: this.maxTokens,
            stream: true,
        });
        for await (const chunk of stream) {
            const delta = chunk.choices[0]?.delta?.content;
            if (delta) {
                yield delta;
            }
        }
    }
    async completeSync(messages) {
        const chunks = [];
        for await (const chunk of this.complete(messages)) {
            chunks.push(chunk);
        }
        return {
            content: chunks.join(""),
            model: this.model,
            provider: this.provider,
            finishReason: "stop",
        };
    }
}
/**
 * Ollama (local) provider implementation.
 */
export class OllamaProvider {
    model;
    host;
    provider = Provider.OLLAMA;
    constructor(model = "qwen2.5", host = process.env.OLLAMA_HOST ?? "http://localhost:11434") {
        this.model = model;
        this.host = host;
    }
    async *complete(messages) {
        const { Ollama } = await import("ollama");
        const client = new Ollama({ host: this.host });
        const response = await client.chat({
            model: this.model,
            messages: messages.map((m) => ({
                role: m.role,
                content: m.content,
            })),
            stream: true,
        });
        for await (const chunk of response) {
            if (chunk.message?.content) {
                yield chunk.message.content;
            }
        }
    }
    async completeSync(messages) {
        const { Ollama } = await import("ollama");
        const client = new Ollama({ host: this.host });
        const response = await client.chat({
            model: this.model,
            messages: messages.map((m) => ({
                role: m.role,
                content: m.content,
            })),
        });
        return {
            content: response.message.content,
            model: this.model,
            provider: this.provider,
            usage: {
                promptTokens: response.prompt_eval_count ?? 0,
                completionTokens: response.eval_count ?? 0,
                totalTokens: (response.prompt_eval_count ?? 0) + (response.eval_count ?? 0),
            },
            finishReason: "stop",
        };
    }
}
/**
 * Model orchestrator that manages multiple providers and handles fallback.
 *
 * Ports the Python ProviderRouter class.
 */
export class ModelOrchestrator {
    providers;
    constructor(configs) {
        this.providers = new Map();
        if (configs) {
            for (const config of configs) {
                this.registerProvider(config);
            }
        }
    }
    /** Register a provider from config */
    registerProvider(config) {
        let provider;
        switch (config.provider) {
            case Provider.ANTHROPIC:
                provider = new AnthropicProvider(config.model, config.apiKey, config.baseUrl, config.maxTokens);
                break;
            case Provider.OPENAI:
                provider = new OpenAIProvider(config.model, config.apiKey, config.maxTokens);
                break;
            case Provider.OLLAMA:
                provider = new OllamaProvider(config.model, config.baseUrl);
                break;
            default:
                throw new Error(`Unknown provider: ${config.provider}`);
        }
        this.providers.set(config.provider, provider);
    }
    /** Stream responses from a provider with fallback */
    async *stream(provider, messages) {
        const llm = this.providers.get(provider);
        if (!llm) {
            throw new Error(`Provider ${provider} not registered. Available: ${[...this.providers.keys()].join(", ")}`);
        }
        yield* llm.complete(messages);
    }
    /** Get a synchronous response from a provider */
    async complete(provider, messages) {
        const llm = this.providers.get(provider);
        if (!llm) {
            throw new Error(`Provider ${provider} not registered`);
        }
        return llm.completeSync(messages);
    }
    /** Try providers in fallback order until one succeeds */
    async *streamWithFallback(messages) {
        const errors = [];
        for (const provider of PROVIDER_FALLBACK_ORDER) {
            if (!this.providers.has(provider))
                continue;
            try {
                yield* this.stream(provider, messages);
                return;
            }
            catch (err) {
                errors.push({
                    provider,
                    error: err instanceof Error ? err : new Error(String(err)),
                });
            }
        }
        throw new Error(`All providers failed: ${errors.map((e) => `${e.provider}: ${e.error.message}`).join("; ")}`);
    }
    /** Calculate cost for token usage */
    static calculateCost(provider, usage) {
        const rates = COST_PER_MILLION[provider];
        if (!rates)
            return 0;
        return ((usage.promptTokens * rates.input) / 1_000_000 +
            (usage.completionTokens * rates.output) / 1_000_000);
    }
    /** Get registered provider names */
    getRegisteredProviders() {
        return [...this.providers.keys()];
    }
}
//# sourceMappingURL=models.js.map