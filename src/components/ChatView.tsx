/**
 * Chat message view component for rendering conversation history.
 */

import React from "react";
import { Box, Text } from "ink";
import type { Message } from "../types/message.js";

interface ChatViewProps {
  messages: Message[];
}

interface ChatMessageProps {
  message: Message;
}

/** Role display configuration */
const ROLE_STYLES: Record<string, { label: string; color: string }> = {
  user: { label: "You", color: "green" },
  assistant: { label: "Qarin", color: "cyan" },
  system: { label: "System", color: "yellow" },
  tool: { label: "Tool", color: "magenta" },
};

function ChatMessage({ message }: ChatMessageProps): React.ReactElement {
  const style = ROLE_STYLES[message.role] ?? { label: message.role, color: "white" };

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold color={style.color}>
        {style.label}:
      </Text>
      <Box marginLeft={2}>
        <Text wrap="wrap">{message.content}</Text>
      </Box>
    </Box>
  );
}

export function ChatView({ messages }: ChatViewProps): React.ReactElement {
  const visibleMessages = messages.filter((m) => m.role !== "system");

  if (visibleMessages.length === 0) {
    return (
      <Box>
        <Text dimColor>No messages yet. Type a message to get started.</Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      {visibleMessages.map((msg, i) => (
        <ChatMessage key={i} message={msg} />
      ))}
    </Box>
  );
}
