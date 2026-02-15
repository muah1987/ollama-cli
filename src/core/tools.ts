/**
 * Tool execution module.
 *
 * Ports the Python skills/tools.py into TypeScript.
 * Provides file operations, shell execution, and search capabilities.
 */

import { readFile, writeFile, access } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { resolve, dirname } from "node:path";

import type { ToolResult } from "../types/agent.js";

const execFileAsync = promisify(execFile);

/** Maximum output length for shell commands */
const MAX_OUTPUT_LENGTH = 50_000;

/** Maximum file size to read (10MB) */
const MAX_FILE_SIZE = 10 * 1024 * 1024;

/**
 * Read the contents of a file.
 */
export async function fileRead(path: string): Promise<ToolResult> {
  try {
    const resolvedPath = resolve(path);
    await access(resolvedPath);
    const content = await readFile(resolvedPath, "utf-8");

    if (content.length > MAX_FILE_SIZE) {
      return {
        success: false,
        output: "",
        error: `File too large: ${content.length} bytes (max: ${MAX_FILE_SIZE})`,
      };
    }

    return { success: true, output: content };
  } catch (err) {
    return {
      success: false,
      output: "",
      error: `Failed to read file: ${err instanceof Error ? err.message : String(err)}`,
    };
  }
}

/**
 * Write content to a file, creating directories as needed.
 */
export async function fileWrite(path: string, content: string): Promise<ToolResult> {
  try {
    const resolvedPath = resolve(path);
    const { mkdir } = await import("node:fs/promises");
    await mkdir(dirname(resolvedPath), { recursive: true });
    await writeFile(resolvedPath, content, "utf-8");
    return { success: true, output: `Written ${content.length} bytes to ${path}` };
  } catch (err) {
    return {
      success: false,
      output: "",
      error: `Failed to write file: ${err instanceof Error ? err.message : String(err)}`,
    };
  }
}

/**
 * Edit a range of lines in a file.
 */
export async function fileEdit(
  path: string,
  startLine: number,
  endLine: number,
  newContent: string,
): Promise<ToolResult> {
  try {
    const resolvedPath = resolve(path);
    const content = await readFile(resolvedPath, "utf-8");
    const lines = content.split("\n");

    if (startLine < 1 || endLine > lines.length || startLine > endLine) {
      return {
        success: false,
        output: "",
        error: `Invalid line range: ${startLine}-${endLine} (file has ${lines.length} lines)`,
      };
    }

    const before = lines.slice(0, startLine - 1);
    const after = lines.slice(endLine);
    const newLines = [...before, newContent, ...after];

    await writeFile(resolvedPath, newLines.join("\n"), "utf-8");
    return {
      success: true,
      output: `Edited lines ${startLine}-${endLine} in ${path}`,
    };
  } catch (err) {
    return {
      success: false,
      output: "",
      error: `Failed to edit file: ${err instanceof Error ? err.message : String(err)}`,
    };
  }
}

/**
 * Execute a shell command with timeout.
 */
export async function shellExec(
  command: string,
  timeoutMs: number = 30_000,
): Promise<ToolResult> {
  try {
    const { stdout, stderr } = await execFileAsync("sh", ["-c", command], {
      timeout: timeoutMs,
      maxBuffer: MAX_OUTPUT_LENGTH,
      env: { ...process.env },
    });

    const output = stdout.slice(0, MAX_OUTPUT_LENGTH);
    return {
      success: true,
      output: output + (stderr ? `\n[stderr]: ${stderr}` : ""),
    };
  } catch (err) {
    const error = err as { stdout?: string; stderr?: string; message: string };
    return {
      success: false,
      output: error.stdout ?? "",
      error: error.stderr ?? error.message,
    };
  }
}

/**
 * Search for a pattern in files using grep.
 */
export async function grepSearch(
  pattern: string,
  directory: string = ".",
): Promise<ToolResult> {
  try {
    const { stdout } = await execFileAsync(
      "grep",
      ["-rn", "--include=*", "-E", pattern, directory],
      { timeout: 15_000, maxBuffer: MAX_OUTPUT_LENGTH },
    );

    return { success: true, output: stdout.slice(0, MAX_OUTPUT_LENGTH) };
  } catch (err) {
    const error = err as { code?: number; stdout?: string; message: string };
    // grep returns exit code 1 for no matches
    if (error.code === 1) {
      return { success: true, output: "No matches found" };
    }
    return {
      success: false,
      output: error.stdout ?? "",
      error: error.message,
    };
  }
}

/**
 * Fetch content from a URL.
 */
export async function webFetch(url: string): Promise<ToolResult> {
  try {
    const response = await fetch(url, {
      headers: { "User-Agent": "qarin-cli/0.1.0" },
      signal: AbortSignal.timeout(15_000),
    });

    if (!response.ok) {
      return {
        success: false,
        output: "",
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const text = await response.text();
    return { success: true, output: text.slice(0, MAX_OUTPUT_LENGTH) };
  } catch (err) {
    return {
      success: false,
      output: "",
      error: `Failed to fetch: ${err instanceof Error ? err.message : String(err)}`,
    };
  }
}

/**
 * Execute a tool by name with the given arguments.
 */
export async function executeTool(
  toolName: string,
  args: Record<string, unknown>,
): Promise<ToolResult> {
  switch (toolName) {
    case "file_read":
      return fileRead(args.path as string);
    case "file_write":
      return fileWrite(args.path as string, args.content as string);
    case "file_edit":
      return fileEdit(
        args.path as string,
        args.startLine as number,
        args.endLine as number,
        args.newContent as string,
      );
    case "shell_exec":
      return shellExec(args.command as string);
    case "grep_search":
      return grepSearch(args.pattern as string, args.directory as string);
    case "web_fetch":
      return webFetch(args.url as string);
    default:
      return {
        success: false,
        output: "",
        error: `Unknown tool: ${toolName}`,
      };
  }
}
