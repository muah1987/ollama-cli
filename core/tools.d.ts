/**
 * Tool execution module.
 *
 * Ports the Python skills/tools.py into TypeScript.
 * Provides file operations, shell execution, and search capabilities.
 */
import type { ToolResult } from "../types/agent.js";
/**
 * Read the contents of a file.
 */
export declare function fileRead(path: string): Promise<ToolResult>;
/**
 * Write content to a file, creating directories as needed.
 */
export declare function fileWrite(path: string, content: string): Promise<ToolResult>;
/**
 * Edit a range of lines in a file.
 */
export declare function fileEdit(path: string, startLine: number, endLine: number, newContent: string): Promise<ToolResult>;
/**
 * Execute a shell command with timeout.
 */
export declare function shellExec(command: string, timeoutMs?: number): Promise<ToolResult>;
/**
 * Search for a pattern in files using grep.
 */
export declare function grepSearch(pattern: string, directory?: string): Promise<ToolResult>;
/**
 * Fetch content from a URL.
 */
export declare function webFetch(url: string): Promise<ToolResult>;
/**
 * Execute a tool by name with the given arguments.
 */
export declare function executeTool(toolName: string, args: Record<string, unknown>): Promise<ToolResult>;
//# sourceMappingURL=tools.d.ts.map