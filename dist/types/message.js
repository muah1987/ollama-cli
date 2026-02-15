/**
 * Message types for multi-provider LLM communication.
 */
/** Supported LLM providers */
export var Provider;
(function (Provider) {
    Provider["ANTHROPIC"] = "anthropic";
    Provider["OPENAI"] = "openai";
    Provider["OLLAMA"] = "ollama";
})(Provider || (Provider = {}));
/** Fallback chain order for provider routing */
export const PROVIDER_FALLBACK_ORDER = [
    Provider.OLLAMA,
    Provider.ANTHROPIC,
    Provider.OPENAI,
];
//# sourceMappingURL=message.js.map