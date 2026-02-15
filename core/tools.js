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
const execFileAsync = promisify(execFile);
/** Maximum output length for shell commands */
const MAX_OUTPUT_LENGTH = 50_000;
/** Maximum file size to read (10MB) */
const MAX_FILE_SIZE = 10 * 1024 * 1024;
/**
 * Read the contents of a file.
 */
export async function fileRead(path) {
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
    }
    catch (err) {
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
export async function fileWrite(path, content) {
    try {
        const resolvedPath = resolve(path);
        const { mkdir } = await import("node:fs/promises");
        await mkdir(dirname(resolvedPath), { recursive: true });
        await writeFile(resolvedPath, content, "utf-8");
        return { success: true, output: `Written ${content.length} bytes to ${path}` };
    }
    catch (err) {
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
export async function fileEdit(path, startLine, endLine, newContent) {
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
    }
    catch (err) {
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
export async function shellExec(command, timeoutMs = 30_000) {
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
    }
    catch (err) {
        const error = err;
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
export async function grepSearch(pattern, directory = ".") {
    try {
        const { stdout } = await execFileAsync("grep", ["-rn", "--include=*", "-E", pattern, directory], { timeout: 15_000, maxBuffer: MAX_OUTPUT_LENGTH });
        return { success: true, output: stdout.slice(0, MAX_OUTPUT_LENGTH) };
    }
    catch (err) {
        const error = err;
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
export async function webFetch(url) {
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
    }
    catch (err) {
        return {
            success: false,
            output: "",
            error: `Failed to fetch: ${err instanceof Error ? err.message : String(err)}`,
        };
    }
}
/**
 * Show git diff (staged/unstaged).
 */
export async function gitDiff(options) {
    try {
        const args = ["diff"];
        if (options?.staged)
            args.push("--staged");
        if (options?.path)
            args.push("--", options.path);
        const { stdout } = await execFileAsync("git", args, {
            timeout: 15_000,
            maxBuffer: MAX_OUTPUT_LENGTH,
        });
        return { success: true, output: stdout || "No changes" };
    }
    catch (err) {
        const error = err;
        return {
            success: false,
            output: error.stdout ?? "",
            error: error.stderr ?? error.message,
        };
    }
}
/**
 * Stage files and commit with a message.
 */
export async function gitCommit(message, files) {
    try {
        // Stage files
        const addArgs = ["add", ...(files?.length ? files : ["."])];
        await execFileAsync("git", addArgs, { timeout: 10_000 });
        // Commit
        const { stdout } = await execFileAsync("git", ["commit", "-m", message], {
            timeout: 15_000,
            maxBuffer: MAX_OUTPUT_LENGTH,
        });
        return { success: true, output: stdout };
    }
    catch (err) {
        const error = err;
        return {
            success: false,
            output: error.stdout ?? "",
            error: error.stderr ?? error.message,
        };
    }
}
/**
 * Search code for a pattern using ripgrep (rg) or grep.
 */
export async function codeSearch(pattern, directory = ".", options) {
    const fileType = options?.fileType;
    try {
        // Try ripgrep first
        const rgArgs = ["-n", "--no-heading"];
        if (fileType)
            rgArgs.push("-t", fileType);
        rgArgs.push(pattern, directory);
        const { stdout } = await execFileAsync("rg", rgArgs, {
            timeout: 15_000,
            maxBuffer: MAX_OUTPUT_LENGTH,
        });
        return { success: true, output: stdout.slice(0, MAX_OUTPUT_LENGTH) };
    }
    catch {
        // Fallback to grep
        return grepSearch(pattern, directory);
    }
}
/**
 * Run the project test suite.
 */
export async function testRun(command) {
    const testCmd = command ?? "npm test";
    try {
        const { stdout, stderr } = await execFileAsync("sh", ["-c", testCmd], {
            timeout: 120_000,
            maxBuffer: MAX_OUTPUT_LENGTH,
            env: { ...process.env, CI: "true" },
        });
        const output = stdout.slice(0, MAX_OUTPUT_LENGTH);
        return {
            success: true,
            output: output + (stderr ? `\n[stderr]: ${stderr.slice(0, 5000)}` : ""),
        };
    }
    catch (err) {
        const error = err;
        return {
            success: false,
            output: error.stdout?.slice(0, MAX_OUTPUT_LENGTH) ?? "",
            error: error.stderr?.slice(0, 5000) ?? error.message,
        };
    }
}
/**
 * Run linter and return structured diagnostics.
 */
export async function lintCheck(command) {
    const lintCmd = command ?? "npx eslint . --format json 2>/dev/null || npx eslint .";
    try {
        const { stdout, stderr } = await execFileAsync("sh", ["-c", lintCmd], {
            timeout: 60_000,
            maxBuffer: MAX_OUTPUT_LENGTH,
            env: { ...process.env },
        });
        return {
            success: true,
            output: stdout.slice(0, MAX_OUTPUT_LENGTH),
        };
    }
    catch (err) {
        const error = err;
        // Lint tools often exit non-zero when issues found
        const output = error.stdout ?? "";
        return {
            success: output.length > 0,
            output: output.slice(0, MAX_OUTPUT_LENGTH),
            error: output.length > 0 ? undefined : (error.stderr ?? error.message),
        };
    }
}
/**
 * Streaming shell execution -- runs a command and emits output line-by-line.
 *
 * @param command - Shell command to run
 * @param onLine - Callback for each line of output
 * @param options - cwd override, timeout
 * @returns ToolResult
 */
export async function shellExecStreaming(command, onLine, options) {
    return new Promise((res) => {
        const { spawn } = require("node:child_process");
        const child = spawn("sh", ["-c", command], {
            cwd: options?.cwd ?? process.cwd(),
            env: { ...process.env },
            timeout: options?.timeout ?? 60_000,
        });
        const chunks = [];
        let errorOutput = "";
        child.stdout?.on("data", (data) => {
            const text = data.toString();
            chunks.push(text);
            const lines = text.split("\n");
            for (const line of lines) {
                if (line)
                    onLine(line, "stdout");
            }
        });
        child.stderr?.on("data", (data) => {
            const text = data.toString();
            errorOutput += text;
            const lines = text.split("\n");
            for (const line of lines) {
                if (line)
                    onLine(line, "stderr");
            }
        });
        child.on("close", (code) => {
            res({
                success: code === 0,
                output: chunks.join("").slice(0, MAX_OUTPUT_LENGTH),
                error: code !== 0 ? errorOutput.slice(0, 5000) : undefined,
            });
        });
        child.on("error", (err) => {
            res({
                success: false,
                output: chunks.join(""),
                error: err.message,
            });
        });
    });
}
/** Destructive command patterns for confirmation */
const DESTRUCTIVE_PATTERNS = [
    /\brm\s+(-rf?|--recursive)/,
    /\bgit\s+push\s+--force/,
    /\bgit\s+reset\s+--hard/,
    /\bdrop\s+(table|database)/i,
    /\btruncate\s+table/i,
    /\bformat\s+/,
    /\bmkfs\./,
    /\bdd\s+if=/,
];
/**
 * Check if a command is destructive and needs confirmation.
 */
export function isDestructiveCommand(command) {
    return DESTRUCTIVE_PATTERNS.some((p) => p.test(command));
}
/** Working directory tracker */
let _currentWorkingDir = process.cwd();
export function getWorkingDir() {
    return _currentWorkingDir;
}
export function setWorkingDir(dir) {
    _currentWorkingDir = resolve(dir);
}
/**
 * Execute a tool by name with the given arguments.
 *
 * Supports both built-in tools and dynamically loaded plugins.
 */
export async function executeTool(toolName, args, pluginRegistry) {
    switch (toolName) {
        case "file_read":
            return fileRead(args.path);
        case "file_write":
            return fileWrite(args.path, args.content);
        case "file_edit":
            return fileEdit(args.path, args.startLine, args.endLine, args.newContent);
        case "shell_exec":
            return shellExec(args.command);
        case "grep_search":
            return grepSearch(args.pattern, args.directory);
        case "web_fetch":
            return webFetch(args.url);
        case "git_diff":
            return gitDiff(args);
        case "git_commit":
            return gitCommit(args.message, args.files);
        case "code_search":
            return codeSearch(args.pattern, args.directory, args);
        case "test_run":
            return testRun(args.command);
        case "lint_check":
            return lintCheck(args.command);
        default: {
            // Check plugin registry
            if (pluginRegistry) {
                const plugin = pluginRegistry.get(toolName);
                if (plugin) {
                    return plugin.execute(args);
                }
            }
            return {
                success: false,
                output: "",
                error: `Unknown tool: ${toolName}`,
            };
        }
    }
}
//# sourceMappingURL=tools.js.map