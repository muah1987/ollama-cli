/**
 * Session persistence module.
 *
 * Ports the Python model/session.py into TypeScript.
 * Manages session state with save/load for continuity across runs,
 * QARIN.md project context seeding, and session summary tracking.
 */

import { readFile, writeFile, mkdir, access } from "node:fs/promises";
import { resolve, join } from "node:path";

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
    this.sessionId = options.sessionId ?? crypto.randomUUID().slice(0, 12);
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
    const dir = resolvedPath.substring(0, resolvedPath.lastIndexOf("/"));
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

    // Rebuild TokenCounter
    const tokenData = data.tokenCounter as Record<string, number>;
    const tokenCounter = new TokenCounter(
      data.provider,
      tokenData.contextMax as number,
    );

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

  /** Look for QARIN.md in the current directory and parent dirs */
  private async findQarinMd(): Promise<string | null> {
    let current = process.cwd();
    for (let i = 0; i < 5; i++) {
      const candidate = join(current, QARIN_MD);
      try {
        await access(candidate);
        return candidate;
      } catch {
        const parent = resolve(current, "..");
        if (parent === current) break;
        current = parent;
      }
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
    } catch {
      // Ignore write errors
    }
  }
}
