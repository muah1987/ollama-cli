/**
 * Agent and session types for the qarin-cli core.
 */

import type { Message, Provider, TokenUsage, ToolDefinition } from "./message.js";
import type { OperationPhase, ThemeName } from "./theme.js";

/** CLI options from commander */
export interface CLIOptions {
  model: string;
  provider: string;
  theme: ThemeName;
  print?: boolean;
  resume?: boolean;
  systemPrompt?: string;
  outputFormat?: "text" | "json" | "markdown";
}

/** Session configuration */
export interface SessionConfig {
  sessionId: string;
  model: string;
  provider: Provider;
  maxContextLength: number;
  compactThreshold: number;
  autoCompact: boolean;
  keepLastN: number;
}

/** Session status snapshot */
export interface SessionStatus {
  sessionId: string;
  model: string;
  provider: Provider;
  messageCount: number;
  contextUsage: ContextUsage;
  tokenUsage: TokenUsage;
  startTime: string;
  duration: number;
}

/** Context window usage */
export interface ContextUsage {
  used: number;
  max: number;
  percent: number;
}

/** Agent type classification */
export type AgentType =
  | "code"
  | "review"
  | "test"
  | "debug"
  | "plan"
  | "docs"
  | "research"
  | "orchestrator";

/** Intent classification result */
export interface IntentResult {
  agentType: AgentType;
  confidence: number;
  matchedPatterns: string[];
  explanation?: string;
}

/** Agent model assignment from settings */
export interface AgentModelConfig {
  provider: Provider;
  model: string;
}

/** Tool execution result */
export interface ToolResult {
  success: boolean;
  output: string;
  error?: string;
}

/** Hook execution result */
export interface HookResult {
  success: boolean;
  stdout: string;
  stderr: string;
  returnCode: number;
  parsed?: Record<string, unknown>;
  error?: string;
}

/** Sub-agent wave definition */
export interface Wave {
  waveNumber: number;
  agents: string[];
  results: Record<string, unknown>[];
  status: "pending" | "running" | "completed" | "failed";
  timestamp?: string;
}

/** Shared state for sub-agent orchestration */
export interface SharedState {
  userInput: string;
  constraints: string[];
  analysisResults: Record<string, unknown>;
  plan: Record<string, unknown>;
  executionOutputs: Record<string, unknown>[];
  status: string;
}

/** Memory entry for persistent knowledge */
export interface MemoryEntry {
  key: string;
  content: string;
  category: "fact" | "preference" | "context" | "learned";
  importance: number;
  tokenCost: number;
  createdAt: string;
  lastAccessed: string;
  accessCount: number;
}

/** Agent-to-agent message */
export interface AgentMessage {
  sender: string;
  recipient: string;
  content: string;
  messageType: string;
  timestamp: string;
  tokenCost: number;
}

/** Available built-in tools */
export const BUILT_IN_TOOLS: ToolDefinition[] = [
  {
    name: "file_read",
    description: "Read the contents of a file",
    parameters: {
      type: "object",
      properties: {
        path: { type: "string", description: "Path to file" },
      },
      required: ["path"],
    },
  },
  {
    name: "file_write",
    description: "Write content to a file",
    parameters: {
      type: "object",
      properties: {
        path: { type: "string", description: "Path to file" },
        content: { type: "string", description: "Content to write" },
      },
      required: ["path", "content"],
    },
  },
  {
    name: "file_edit",
    description: "Edit a range of lines in a file",
    parameters: {
      type: "object",
      properties: {
        path: { type: "string", description: "Path to file" },
        startLine: { type: "number", description: "Start line (1-based)" },
        endLine: { type: "number", description: "End line (1-based)" },
        newContent: { type: "string", description: "Replacement content" },
      },
      required: ["path", "startLine", "endLine", "newContent"],
    },
  },
  {
    name: "shell_exec",
    description: "Execute a shell command",
    parameters: {
      type: "object",
      properties: {
        command: { type: "string", description: "Command to execute" },
      },
      required: ["command"],
    },
  },
  {
    name: "grep_search",
    description: "Search for a pattern in files",
    parameters: {
      type: "object",
      properties: {
        pattern: { type: "string", description: "Regex pattern" },
        directory: { type: "string", description: "Directory to search" },
      },
      required: ["pattern"],
    },
  },
  {
    name: "web_fetch",
    description: "Fetch content from a URL",
    parameters: {
      type: "object",
      properties: {
        url: { type: "string", description: "URL to fetch" },
      },
      required: ["url"],
    },
  },
];
