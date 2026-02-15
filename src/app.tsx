/**
 * Main Ink application component.
 *
 * Renders the full chat interface with status bar, messages,
 * themed progress, intent badge, token display, and input area.
 */

import React, { useState, useCallback } from "react";
import { Box, Text, useApp } from "ink";
import type { CLIOptions } from "./types/agent.js";
import type { Message } from "./types/message.js";
import { useAgent } from "./hooks/useAgent.js";
import { useTheme } from "./hooks/useTheme.js";
import { StatusBar } from "./components/StatusBar.js";
import { ChatView } from "./components/ChatView.js";
import { ProgressTheme } from "./components/ProgressTheme.js";
import { InputArea } from "./components/InputArea.js";
import { Session } from "./core/session.js";

interface QarinAppProps {
  task?: string;
  options: CLIOptions;
}

/** Load the latest session's messages from .qarin/sessions/ */
async function loadLatestSession(): Promise<Message[]> {
  const { readdir, readFile } = await import("node:fs/promises");
  const { join, resolve } = await import("node:path");

  const sessionsDir = resolve(".qarin/sessions");
  try {
    const files = await readdir(sessionsDir);
    const jsonFiles = files.filter((f) => f.endsWith(".json")).sort().reverse();
    if (jsonFiles.length === 0) return [];

    const content = await readFile(join(sessionsDir, jsonFiles[0]), "utf-8");
    const data = JSON.parse(content) as { contextManager?: { messages?: Message[] } };
    return data.contextManager?.messages ?? [];
  } catch {
    return [];
  }
}

export default function QarinApp({ task, options }: QarinAppProps): React.ReactElement {
  const { exit } = useApp();
  const { theme, nextTheme } = useTheme(options.theme);
  const {
    phase,
    details,
    isProcessing,
    streamOutput,
    status,
    intent,
    tokenDisplay,
    error,
    sendMessage,
    endSession,
  } = useAgent(options);

  const [messages, setMessages] = useState<Message[]>([]);
  const [resumeLoaded, setResumeLoaded] = useState(false);

  // Handle --resume: load the latest session on mount
  React.useEffect(() => {
    if (options.resume && !resumeLoaded) {
      setResumeLoaded(true);
      loadLatestSession().then((msgs) => {
        if (msgs.length > 0) {
          setMessages(msgs);
        } else {
          setMessages([{ role: "system", content: "No previous session found." }]);
        }
      }).catch(() => {
        setMessages([{ role: "system", content: "Failed to load previous session." }]);
      });
    }
  }, []);

  const handleSubmit = useCallback(
    async (text: string) => {
      if (text === "/quit" || text === "/exit") {
        await endSession();
        exit();
        return;
      }

      if (text === "/save") {
        const session = new Session({
          model: options.model,
          provider: options.provider,
        });
        const savePath = await session.save();
        setMessages((prev) => [...prev, { role: "system", content: `Session saved to ${savePath}` }]);
        return;
      }

      if (text === "/theme") {
        nextTheme();
        return;
      }

      if (text === "/status") {
        const statusMsg = status
          ? `Session: ${status.sessionId}\nModel: ${status.provider}/${status.model}\nMessages: ${status.messageCount}\nTokens: ${status.tokenUsage.totalTokens.toLocaleString()}\nContext: ${status.contextUsage.percent}%`
          : "No active session";
        setMessages((prev) => [...prev, { role: "system", content: statusMsg }]);
        return;
      }

      // Add user message to display
      setMessages((prev) => [...prev, { role: "user", content: text }]);

      // Send to agent
      await sendMessage(text);
    },
    [sendMessage, endSession, nextTheme, exit, status],
  );

  // If a task was passed as an argument, execute it immediately
  React.useEffect(() => {
    if (task) {
      handleSubmit(task).catch((err: unknown) => {
        // Display error if initial task fails
        const message = err instanceof Error ? err.message : String(err);
        setMessages((prev) => [...prev, { role: "system", content: `Error: ${message}` }]);
      });
    }
  }, []);

  // Append assistant responses to messages
  React.useEffect(() => {
    if (streamOutput && !isProcessing) {
      setMessages((prev) => [...prev, { role: "assistant", content: streamOutput }]);
    }
  }, [isProcessing, streamOutput]);

  return (
    <Box flexDirection="column" height="100%">
      {/* Status Bar */}
      <StatusBar status={status} theme={theme} />

      {/* Chat Messages */}
      <Box flexDirection="column" flexGrow={1} paddingX={1} marginY={1}>
        <ChatView messages={messages} />

        {/* Streaming output */}
        {isProcessing && streamOutput && (
          <Box marginLeft={2}>
            <Text color="cyan">{streamOutput}</Text>
          </Box>
        )}
      </Box>

      {/* Intent Badge */}
      {intent && intent.confidence > 0 && (
        <Box paddingX={1}>
          <Text dimColor>
            Intent: {intent.agentType} ({(intent.confidence * 100).toFixed(0)}%)
            {intent.matchedPatterns.length > 0 &&
              ` [${intent.matchedPatterns.slice(0, 3).join(", ")}]`}
          </Text>
        </Box>
      )}

      {/* Progress Indicator */}
      {isProcessing && (
        <Box paddingX={1}>
          <ProgressTheme theme={theme} phase={phase} details={details} />
        </Box>
      )}

      {/* Token Display */}
      {tokenDisplay && !isProcessing && (
        <Box paddingX={1}>
          <Text dimColor>{tokenDisplay}</Text>
        </Box>
      )}

      {/* Error Display */}
      {error && (
        <Box paddingX={1}>
          <Text color="red">Error: {error.message}</Text>
        </Box>
      )}

      {/* Input Area */}
      <InputArea
        onSubmit={handleSubmit}
        placeholder="Type a message... (/quit, /theme, /status, /save)"
        disabled={isProcessing}
      />
    </Box>
  );
}
