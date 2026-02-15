#!/usr/bin/env node
/**
 * CLI entry point for qarin-cli TypeScript version.
 *
 * Uses Commander for argument parsing and Ink for the terminal UI.
 */

import React from "react";
import { render } from "ink";
import { Command } from "commander";
import QarinApp from "./app.js";
import type { CLIOptions } from "./types/agent.js";
import type { ThemeName } from "./types/theme.js";
import { getAvailableThemes } from "./themes/index.js";

const program = new Command();

program
  .name("qarin")
  .version("0.1.0")
  .description("AI coding assistant with Arabic-themed progress indicators")
  .argument("[task]", "Task to execute (optional, enters interactive mode if omitted)")
  .option("-m, --model <model>", "AI model to use", "claude-sonnet-4-20250514")
  .option("-p, --provider <provider>", "LLM provider (anthropic, openai, ollama)", "anthropic")
  .option(
    "-t, --theme <theme>",
    `Progress theme (${getAvailableThemes().join(", ")})`,
    "shisha",
  )
  .option("--print", "Non-interactive output mode")
  .option("--resume", "Resume the latest session")
  .option("--system-prompt <prompt>", "Custom system prompt")
  .option(
    "--output-format <format>",
    "Output format: text, json, markdown",
    "text",
  )
  .action((task: string | undefined, opts: Record<string, string | boolean | undefined>) => {
    const options: CLIOptions = {
      model: opts.model as string,
      provider: opts.provider as string,
      theme: opts.theme as ThemeName,
      print: opts.print as boolean | undefined,
      resume: opts.resume as boolean | undefined,
      systemPrompt: opts.systemPrompt as string | undefined,
      outputFormat: opts.outputFormat as CLIOptions["outputFormat"],
    };

    render(<QarinApp task={task} options={options} />);
  });

program.parse();
