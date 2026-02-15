/**
 * Hook runner module.
 *
 * Ports the Python server/hook_runner.py into TypeScript.
 * Loads hook configuration from settings.json and dispatches
 * events to hook commands via subprocess.
 */

import { readFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { resolve, join } from "node:path";

import type { HookResult } from "../types/agent.js";

const execFileAsync = promisify(execFile);

/** Hook definition from settings.json */
interface HookDefinition {
  type: string;
  command: string;
}

/** Hook entry from settings.json */
interface HookEntry {
  matcher: string;
  hooks: HookDefinition[];
}

/** Settings file structure */
interface SettingsData {
  hooks?: Record<string, HookEntry[]>;
}

/**
 * Hook runner that loads settings.json and executes hook commands.
 *
 * Supports 13 lifecycle events matching the Python implementation:
 * - SessionStart, SessionEnd
 * - PreToolUse, PostToolUse, PostToolUseFailure
 * - PreCompact
 * - UserPromptSubmit
 * - SkillTrigger
 * - SubagentStart, SubagentStop
 * - Notification
 * - PermissionRequest
 * - Stop
 */
export class HookRunner {
  private hooks: Record<string, HookEntry[]> = {};
  private readonly settingsPath: string;

  constructor(settingsPath?: string) {
    this.settingsPath =
      settingsPath ??
      resolve(
        process.env.QARIN_PROJECT_DIR ?? process.cwd(),
        ".qarin",
        "settings.json",
      );
  }

  /** Load hook configuration from settings.json */
  async load(): Promise<void> {
    try {
      const content = await readFile(this.settingsPath, "utf-8");
      const data = JSON.parse(content) as SettingsData;
      this.hooks = data.hooks ?? {};
    } catch {
      this.hooks = {};
    }
  }

  /** Check if hooks are enabled (settings file has hooks) */
  isEnabled(): boolean {
    return Object.keys(this.hooks).length > 0;
  }

  /**
   * Execute all hooks registered for an event name.
   *
   * @param eventName - The event name (e.g. "PreToolUse", "SessionStart")
   * @param payload - JSON-serializable data sent to the hook on stdin
   * @param timeout - Maximum seconds to wait for each hook command
   * @returns List of HookResult, one per matching hook command
   */
  async runHook(
    eventName: string,
    payload: Record<string, unknown>,
    timeout = 30,
  ): Promise<HookResult[]> {
    const results: HookResult[] = [];
    const hookEntries = this.hooks[eventName] ?? [];

    for (const entry of hookEntries) {
      const matcher = entry.matcher ?? "";
      const commands = entry.hooks ?? [];

      // Matcher filtering: empty string matches everything
      if (matcher && !this.matches(matcher, payload)) {
        continue;
      }

      for (const hookDef of commands) {
        if (hookDef.type !== "command") continue;
        if (!hookDef.command) continue;

        const result = await this.executeCommand(
          hookDef.command,
          payload,
          timeout,
        );
        results.push(result);
      }
    }

    return results;
  }

  /** Check if a matcher pattern matches the payload */
  private matches(
    matcher: string,
    payload: Record<string, unknown>,
  ): boolean {
    if (!matcher) return true;

    // Prefer camelCase `toolName` for TypeScript callers, but also support
    // snake_case `tool_name` for compatibility with the Python implementation.
    const toolName =
      (payload.toolName as string | undefined) ??
      (payload.tool_name as string | undefined) ??
      "";

    return matcher === toolName || toolName.includes(matcher);
  }

  /** Run a single hook command via subprocess */
  private async executeCommand(
    command: string,
    payload: Record<string, unknown>,
    timeout: number,
  ): Promise<HookResult> {
    // Expand environment variables in command
    const expandedCommand = command.replace(
      /\$([A-Z_][A-Z0-9_]*)/g,
      (_, name: string) => process.env[name] ?? "",
    );

    const payloadJson = JSON.stringify(payload);

    try {
      const { stdout, stderr } = await new Promise<{
        stdout: string;
        stderr: string;
      }>((resolvePromise, rejectPromise) => {
        const child = execFile(
          "sh",
          ["-c", expandedCommand],
          {
            timeout: timeout * 1000,
            maxBuffer: 50_000,
            env: { ...process.env },
          },
          (error, childStdout, childStderr) => {
            if (error) {
              const err = error as {
                code?: number;
                stdout?: string;
                stderr?: string;
                message: string;
                killed?: boolean;
              };
              err.stdout = childStdout;
              err.stderr = childStderr;
              rejectPromise(err);
              return;
            }

            resolvePromise({ stdout: childStdout, stderr: childStderr });
          },
        );

        if (child.stdin) {
          // Handle EPIPE errors when the command doesn't read stdin
          child.stdin.on("error", () => {
            // Ignore EPIPE errors silently
          });
          child.stdin.write(payloadJson);
          child.stdin.end();
        }
      });

      // Try to parse stdout as JSON
      let parsed: Record<string, unknown> = {};
      const trimmedStdout = stdout.trim();
      if (trimmedStdout) {
        try {
          parsed = JSON.parse(trimmedStdout) as Record<string, unknown>;
        } catch {
          // Not JSON, ignore
        }
      }

      return {
        success: true,
        stdout,
        stderr,
        returnCode: 0,
        parsed,
      };
    } catch (err) {
      const error = err as {
        code?: number;
        stdout?: string;
        stderr?: string;
        message: string;
        killed?: boolean;
      };

      if (error.killed) {
        return {
          success: false,
          stdout: "",
          stderr: "",
          returnCode: -1,
          error: `Hook timed out after ${timeout}s: ${command}`,
        };
      }

      return {
        success: false,
        stdout: error.stdout ?? "",
        stderr: error.stderr ?? "",
        returnCode: error.code ?? -1,
        error: `Hook execution failed: ${error.message}`,
      };
    }
  }
}
