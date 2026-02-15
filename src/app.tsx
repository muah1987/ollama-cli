/**
 * Main Ink application component.
 *
 * Renders the full chat interface with status bar, messages,
 * themed progress, and input area.
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

interface QarinAppProps {
  task?: string;
  options: CLIOptions;
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
    error,
    sendMessage,
  } = useAgent(options);

  const [messages, setMessages] = useState<Message[]>([]);

  const handleSubmit = useCallback(
    async (text: string) => {
      if (text === "/quit" || text === "/exit") {
        exit();
        return;
      }

      if (text === "/theme") {
        nextTheme();
        return;
      }

      // Add user message to display
      setMessages((prev) => [...prev, { role: "user", content: text }]);

      // Send to agent
      await sendMessage(text);
    },
    [sendMessage, nextTheme, exit],
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

      {/* Progress Indicator */}
      {isProcessing && (
        <Box paddingX={1}>
          <ProgressTheme theme={theme} phase={phase} details={details} />
        </Box>
      )}

      {/* Error Display */}
      {error && (
        <Box paddingX={1}>
          <Text color="red">❌ {error.message}</Text>
        </Box>
      )}

      {/* Input Area */}
      <InputArea
        onSubmit={handleSubmit}
        placeholder="Type a message... (/quit to exit, /theme to cycle)"
        disabled={isProcessing}
      />
    </Box>
  );
}
