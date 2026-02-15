#!/usr/bin/env node
import { jsx as _jsx } from "react/jsx-runtime";
import { render } from "ink";
import { Command } from "commander";
import QarinApp from "./app.js";
import { getAvailableThemes } from "./themes/index.js";
const program = new Command();
program
    .name("qarin")
    .version("0.1.0")
    .description("AI coding assistant with Arabic-themed progress indicators")
    .argument("[task]", "Task to execute (optional, enters interactive mode if omitted)")
    .option("-m, --model <model>", "AI model to use", "claude-sonnet-4-20250514")
    .option("-p, --provider <provider>", "LLM provider (anthropic, openai, ollama)", "anthropic")
    .option("-t, --theme <theme>", `Progress theme (${getAvailableThemes().join(", ")})`, "shisha")
    .option("--print", "Non-interactive output mode")
    .option("--resume", "Resume the latest session")
    .option("--system-prompt <prompt>", "Custom system prompt")
    .option("--output-format <format>", "Output format: text, json, markdown", "text")
    .action((task, opts) => {
    const options = {
        model: opts.model,
        provider: opts.provider,
        theme: opts.theme,
        print: opts.print,
        resume: opts.resume,
        systemPrompt: opts.systemPrompt,
        outputFormat: opts.outputFormat,
    };
    render(_jsx(QarinApp, { task: task, options: options }));
});
program.parse();
//# sourceMappingURL=index.js.map