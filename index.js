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
    .action(async (task, opts) => {
    const options = {
        model: opts.model,
        provider: opts.provider,
        theme: opts.theme,
        print: opts.print,
        resume: opts.resume,
        systemPrompt: opts.systemPrompt,
        outputFormat: opts.outputFormat,
    };
    // --print mode: non-interactive, stream to stdout, exit on completion
    if (opts.print && task) {
        const { QarinAgent } = await import("./core/agent.js");
        const agent = new QarinAgent(options);
        agent.on("stream", (chunk) => {
            process.stdout.write(chunk);
        });
        agent.on("toolUse", ({ tool, args }) => {
            if (opts.outputFormat === "json") {
                process.stderr.write(JSON.stringify({ event: "tool_use", tool, args }) + "\n");
            }
            else {
                process.stderr.write(`[tool: ${tool}]\n`);
            }
        });
        try {
            const response = await agent.executeWithTools(task);
            if (opts.outputFormat === "json") {
                const status = agent.getStatus();
                process.stdout.write("\n" + JSON.stringify({
                    response,
                    tokens: status.tokenUsage,
                    model: status.model,
                    provider: status.provider,
                }) + "\n");
            }
            else if (opts.outputFormat === "markdown") {
                // Response already streamed; add trailing newline
                process.stdout.write("\n");
            }
            else {
                process.stdout.write("\n");
            }
            await agent.end();
            process.exit(0);
        }
        catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            process.stderr.write(`Error: ${message}\n`);
            process.exit(1);
        }
        return;
    }
    // Interactive mode: render Ink UI
    render(_jsx(QarinApp, { task: task, options: options }));
});
program.parse();
//# sourceMappingURL=index.js.map
