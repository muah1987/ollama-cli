/**
 * Multi-provider model abstraction layer.
 *
 * Ports the Python providers/ directory into a single unified module
 * with async generator streaming support and tool-call extraction.
 */
import { Provider, PROVIDER_FALLBACK_ORDER } from "../types/message.js";
/** Cost per million tokens by provider */
const COST_PER_MILLION = {
    [Provider.ANTHROPIC]: { input: 3.0, output: 15.0 },
    [Provider.OPENAI]: { input: 5.0, output: 15.0 },
    [Provider.OLLAMA]: { input: 0.0, output: 0.0 },
};
/**
 * Format messages for the Anthropic API.
 *
 * Converts tool_calls on assistant messages to tool_use content blocks,
 * and tool-result messages to user messages with tool_result content type.
 * Merges consecutive tool results into a single user message.
 */
function formatMessagesForAnthropic(messages) {
    const apiMessages = [];
    const systemMessage = messages.find((m) => m.role === "system")?.content;
    let pendingToolResults = [];
    for (const msg of messages) {
        if (msg.role === "system")
            continue;
        // Flush pending tool results before a non-tool message
        if (msg.role !== "tool" && pendingToolResults.length > 0) {
            apiMessages.push({ role: "user", content: pendingToolResults });
            pendingToolResults = [];
        }
        if (msg.role === "assistant" && msg.tool_calls?.length > 0) {
            const content = [];
            if (msg.content) {
                content.push({ type: "text", text: msg.content });
            }
            for (const tc of msg.tool_calls) {
                let input;
                try {
                    input = JSON.parse(tc.function.arguments);
                }
                catch {
                    input = {};
                }
                content.push({
                    type: "tool_use",
                    id: tc.id,
                    name: tc.function.name,
                    input,
                });
            }
            apiMessages.push({ role: "assistant", content });
        }
        else if (msg.role === "tool") {
            pendingToolResults.push({
                type: "tool_result",
                tool_use_id: msg.tool_call_id,
                content: msg.content,
            });
        }
        else {
            apiMessages.push({ role: msg.role, content: msg.content });
        }
    }
    // Flush remaining tool results
    if (pendingToolResults.length > 0) {
        apiMessages.push({ role: "user", content: pendingToolResults });
    }
    return { apiMessages, systemMessage };
}
/**
 * Format messages for the OpenAI API.
 *
 * Passes tool_calls through on assistant messages and converts
 * tool-result messages to role:"tool" with tool_call_id.
 */
function formatMessagesForOpenAI(messages) {
    return messages.map((m) => {
        if (m.role === "tool") {
            return {
                role: "tool",
                tool_call_id: m.tool_call_id,
                content: m.content,
            };
        }
        if (m.role === "assistant" && m.tool_calls?.length > 0) {
            return {
                role: "assistant",
                content: m.content || null,
                tool_calls: m.tool_calls,
            };
        }
        return { role: m.role, content: m.content };
    });
}
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
    async completeSync(messages, tools) {
        const { default: Anthropic } = await import("@anthropic-ai/sdk");
        const client = new Anthropic({ apiKey: this.apiKey });
        const { apiMessages, systemMessage } = formatMessagesForAnthropic(messages);
        const anthropicTools = tools?.map((t) => ({
            name: t.name,
            description: t.description,
            input_schema: t.parameters,
        }));
        const response = await client.messages.create({
            model: this.model,
            max_tokens: this.maxTokens,
            messages: apiMessages,
            ...(systemMessage ? { system: systemMessage } : {}),
            ...(anthropicTools?.length ? { tools: anthropicTools } : {}),
        });
        // Extract text content and tool calls from response content blocks
        let textContent = "";
        const toolCalls = [];
        for (const block of response.content) {
            if (block.type === "text") {
                textContent += block.text;
            }
            else if (block.type === "tool_use") {
                toolCalls.push({
                    id: block.id,
                    type: "function",
                    function: {
                        name: block.name,
                        arguments: JSON.stringify(block.input),
                    },
                });
            }
        }
        return {
            content: textContent,
            model: this.model,
            provider: this.provider,
            finishReason: response.stop_reason,
            toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
            usage: {
                promptTokens: response.usage.input_tokens,
                completionTokens: response.usage.output_tokens,
                totalTokens: response.usage.input_tokens + response.usage.output_tokens,
            },
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
    async completeSync(messages, tools) {
        const { default: OpenAI } = await import("openai");
        const client = new OpenAI({ apiKey: this.apiKey });
        const apiMessages = formatMessagesForOpenAI(messages);
        const openaiTools = tools?.map((t) => ({
            type: "function",
            function: {
                name: t.name,
                description: t.description,
                parameters: t.parameters,
            },
        }));
        const response = await client.chat.completions.create({
            model: this.model,
            messages: apiMessages,
            max_tokens: this.maxTokens,
            ...(openaiTools?.length ? { tools: openaiTools } : {}),
        });
        const choice = response.choices[0];
        return {
            content: choice.message.content ?? "",
            model: this.model,
            provider: this.provider,
            finishReason: choice.finish_reason,
            toolCalls: choice.message.tool_calls?.length > 0 ? choice.message.tool_calls : undefined,
            usage: response.usage
                ? {
                    promptTokens: response.usage.prompt_tokens,
                    completionTokens: response.usage.completion_tokens,
                    totalTokens: response.usage.total_tokens,
                }
                : undefined,
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
    async completeSync(messages, tools) {
        const { Ollama } = await import("ollama");
        const client = new Ollama({ host: this.host });
        const ollamaTools = tools?.map((t) => ({
            type: "function",
            function: {
                name: t.name,
                description: t.description,
                parameters: t.parameters,
            },
        }));
        const response = await client.chat({
            model: this.model,
            messages: messages.map((m) => ({
                role: m.role,
                content: m.content,
            })),
            ...(ollamaTools?.length ? { tools: ollamaTools } : {}),
        });
        // Convert Ollama tool calls to the unified format
        const toolCalls = response.message.tool_calls?.map((tc, i) => ({
            id: `ollama_${Date.now()}_${i}`,
            type: "function",
            function: {
                name: tc.function.name,
                arguments: JSON.stringify(tc.function.arguments),
            },
        }));
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
            toolCalls: toolCalls?.length > 0 ? toolCalls : undefined,
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
    /** Get a synchronous response from a provider with retry on transient errors */
    async complete(provider, messages, tools) {
        const llm = this.providers.get(provider);
        if (!llm) {
            throw new Error(`Provider ${provider} not registered`);
        }
        const delays = [2000, 4000, 8000, 16000];
        let lastError;
        for (let attempt = 0; attempt <= delays.length; attempt++) {
            try {
                return await llm.completeSync(messages, tools);
            }
            catch (err) {
                lastError = err;
                const status = err?.status ?? err?.response?.status;
                const code = err?.code;
                const isRetryable = status === 429 ||
                    (status >= 500 && status < 600) ||
                    code === "ECONNRESET" ||
                    code === "ECONNREFUSED" ||
                    code === "ETIMEDOUT";
                if (!isRetryable || attempt >= delays.length) {
                    throw err;
                }
                await new Promise((resolve) => setTimeout(resolve, delays[attempt]));
            }
        }
        throw lastError;
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
