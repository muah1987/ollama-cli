/**
 * Session persistence module.
 *
 * Ports the Python model/session.py into TypeScript.
 * Manages session state with save/load for continuity across runs,
 * QARIN.md project context seeding, and session summary tracking.
 */

import { readFile, writeFile, mkdir, access } from "node:fs/promises";
import { resolve, join, dirname } from "node:path";
import { randomUUID } from "node:crypto";

import type { Message } from "../types/message.js";
import type { SessionStatus } from "../types/agent.js";
import { ContextManager } from "./context.js";
import { TokenCounter } from "./tokens.js";

const SESSIONS_DIR = ".qarin/sessions";
const QARIN_MD = "QARIN.md";

/** Serialized session data for persistence */
interface SessionData {
  sessionId: string;
  model: string;
  provider: string;
  hooksEnabled: boolean;
  startTime: string | null;
  endTime: string | null;
  messageCount: number;
  tokenCounter: Record<string, unknown>;
  contextManager: {
    systemMessage: string | null;
    messages: Message[];
    maxContextLength: number;
  };
  savedAt: string;
}

/**
 * Session manager with persistence and QARIN.md integration.
 *
 * Coordinates the ContextManager and TokenCounter, handles QARIN.md
 * project context seeding, and provides save/load for continuity.
 */
export class Session {
  readonly sessionId: string;
  readonly model: string;
  readonly provider: string;
  readonly context: ContextManager;
  readonly tokenCounter: TokenCounter;
  readonly hooksEnabled: boolean;

  private startTime: Date | null = null;
  private endTime: Date | null = null;
  private _messageCount = 0;

  constructor(options: {
    sessionId?: string;
    model?: string;
    provider?: string;
    context?: ContextManager;
    tokenCounter?: TokenCounter;
    hooksEnabled?: boolean;
  } = {}) {
    this.sessionId = options.sessionId ?? randomUUID().slice(0, 12);
    this.model = options.model ?? "llama3.2";
    this.provider = options.provider ?? "ollama";
    this.context = options.context ?? new ContextManager();
    this.tokenCounter =
      options.tokenCounter ?? new TokenCounter(this.provider);
    this.hooksEnabled = options.hooksEnabled ?? true;
  }

  get messageCount(): number {
    return this._messageCount;
  }

  /** Start the session, loading QARIN.md context if available */
  async start(): Promise<void> {
    this.startTime = new Date();

    // Build system prompt
    let systemPrompt = [
      "You are Qarin, an AI coding assistant.",
      "You help developers write, debug, test, and improve code.",
      "You have access to file operations, shell commands, and web search.",
      "Be concise, accurate, and helpful.",
      "When writing code, follow the project's existing conventions.",
    ].join("\n");

    // Load QARIN.md project context if available
    const qarinMd = await this.findQarinMd();
    if (qarinMd) {
      try {
        const content = await readFile(qarinMd, "utf-8");
        systemPrompt +=
          "\n\nThe following project context was loaded from QARIN.md:\n\n" +
          content;
      } catch {
        // Ignore read errors
      }
    }

    this.context.setSystemMessage(systemPrompt);
  }

  /** Record a message exchange */
  recordMessage(): void {
    this._messageCount++;
  }

  /** End the session and return a summary */
  async end(): Promise<Record<string, unknown>> {
    this.endTime = new Date();
    const summary = this.buildSummary();

    // Append summary to QARIN.md if it exists
    const qarinMd = await this.findQarinMd();
    if (qarinMd) {
      await this.appendToQarinMd(qarinMd, summary);
    }

    return summary;
  }

  /** Get current session status */
  getStatus(): SessionStatus {
    const now = new Date();
    const duration = this.startTime
      ? (now.getTime() - this.startTime.getTime()) / 1000
      : 0;
    const contextUsage = this.context.getContextUsage();

    return {
      sessionId: this.sessionId,
      model: this.model,
      provider: this.provider as SessionStatus["provider"],
      messageCount: this._messageCount,
      contextUsage,
      tokenUsage: {
        promptTokens: this.tokenCounter.promptTokens,
        completionTokens: this.tokenCounter.completionTokens,
        totalTokens: this.tokenCounter.totalTokens,
      },
      startTime: this.startTime?.toISOString() ?? new Date().toISOString(),
      duration,
    };
  }

  /** Save session state to a JSON file */
  async save(path?: string): Promise<string> {
    const savePath =
      path ??
      join(SESSIONS_DIR, `${this.sessionId}.json`);

    const data: SessionData = {
      sessionId: this.sessionId,
      model: this.model,
      provider: this.provider,
      hooksEnabled: this.hooksEnabled,
      startTime: this.startTime?.toISOString() ?? null,
      endTime: this.endTime?.toISOString() ?? null,
      messageCount: this._messageCount,
      tokenCounter: this.tokenCounter.toJSON(),
      contextManager: {
        systemMessage: null,
        messages: [],
        maxContextLength: 128_000,
        ...this.context.toJSON(),
      },
      savedAt: new Date().toISOString(),
    };

    const resolvedPath = resolve(savePath);
    const dir = dirname(resolvedPath);
    await mkdir(dir, { recursive: true });
    await writeFile(resolvedPath, JSON.stringify(data, null, 2), "utf-8");

    return resolvedPath;
  }

  /** Load a session from a JSON file */
  static async load(sessionId: string, path?: string): Promise<Session> {
    const loadPath =
      path ?? join(SESSIONS_DIR, `${sessionId}.json`);

    const resolvedPath = resolve(loadPath);
    const content = await readFile(resolvedPath, "utf-8");
    const data = JSON.parse(content) as SessionData;

    // Rebuild ContextManager
    const context = ContextManager.fromJSON(
      data.contextManager as Record<string, unknown>,
    );

    // Rebuild TokenCounter with all persisted state
    const tokenData = data.tokenCounter as {
      promptTokens: number;
      completionTokens: number;
      totalTokens?: number;
      tokensPerSecond: number;
      contextUsed: number;
      contextMax: number;
      costEstimate?: number;
      provider: string;
    };
    const tokenCounter = TokenCounter.fromJSON(tokenData);

    const session = new Session({
      sessionId: data.sessionId,
      model: data.model,
      provider: data.provider,
      context,
      tokenCounter,
      hooksEnabled: data.hooksEnabled,
    });

    session._messageCount = data.messageCount;

    if (data.startTime) {
      session.startTime = new Date(data.startTime);
    }
    if (data.endTime) {
      session.endTime = new Date(data.endTime);
    }

    return session;
  }

  /** Format a duration in seconds to human-readable string */
  static formatDuration(seconds: number): string {
    if (seconds < 0) return "0s";
    const total = Math.floor(seconds);
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const secs = total % 60;

    const parts: string[] = [];
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    parts.push(`${secs}s`);
    return parts.join(" ");
  }

  /** Build session summary */
  private buildSummary(): Record<string, unknown> {
    let durationSeconds = 0;
    if (this.startTime && this.endTime) {
      durationSeconds =
        (this.endTime.getTime() - this.startTime.getTime()) / 1000;
    }

    return {
      sessionId: this.sessionId,
      model: this.model,
      provider: this.provider,
      startTime: this.startTime?.toISOString() ?? null,
      endTime: this.endTime?.toISOString() ?? null,
      durationSeconds: Math.round(durationSeconds * 10) / 10,
      durationStr: Session.formatDuration(durationSeconds),
      messages: this._messageCount,
      totalTokens: this.tokenCounter.totalTokens,
      promptTokens: this.tokenCounter.promptTokens,
      completionTokens: this.tokenCounter.completionTokens,
      costEstimate: this.tokenCounter.costEstimate,
    };
  }

  /** Look for QARIN.md in the current directory and parent dirs up to repo root */
  private async findQarinMd(): Promise<string | null> {
    let current = process.cwd();

    // Walk up the directory tree until we reach the filesystem root or a .git marker.
    // At each level, we first check if QARIN.md exists and return it if found.
    // Only if QARIN.md is not found at a level do we check for .git to decide
    // whether to stop searching. This ensures we find QARIN.md in the repo root
    // even when .git is present at the same level.
    for (;;) {
      // Check for QARIN.md at this level first
      const candidate = join(current, QARIN_MD);
      try {
        await access(candidate);
        return candidate; // Found it, return immediately
      } catch {
        // Not found at this level, continue searching
      }

      // Stop if we detect a .git directory, assuming we've reached the repo root
      // and there's no QARIN.md here or in parent directories
      const gitDir = join(current, ".git");
      try {
        await access(gitDir);
        break; // Found .git, stop searching
      } catch {
        // No .git here, continue walking up unless we're at the filesystem root
      }

      const parent = resolve(current, "..");
      if (parent === current) {
        break; // Reached filesystem root
      }
      current = parent;
    }

    return null;
  }

  /** Append a session summary to QARIN.md */
  private async appendToQarinMd(
    qarinMdPath: string,
    summary: Record<string, unknown>,
  ): Promise<void> {
    const entry =
      `\n\n<!-- session:${summary.sessionId} -->\n` +
      `### Session ${summary.sessionId}\n` +
      `- Model: ${summary.model} (${summary.provider})\n` +
      `- Duration: ${summary.durationStr}\n` +
      `- Messages: ${summary.messages}\n` +
      `- Tokens: ${(summary.totalTokens as number).toLocaleString()} ` +
      `(prompt: ${(summary.promptTokens as number).toLocaleString()}, ` +
      `completion: ${(summary.completionTokens as number).toLocaleString()})\n`;

    try {
      const existing = await readFile(qarinMdPath, "utf-8");
      await writeFile(qarinMdPath, existing + entry, "utf-8");
    } catch (error) {
      // Log but do not throw, to avoid crashing on non-critical QARIN.md failures
      console.warn(
        `Failed to append session summary to QARIN.md at "${qarinMdPath}":`,
        error,
      );
    }
  }
}
