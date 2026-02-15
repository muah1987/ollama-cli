/**
 * Status bar component showing session info, model, theme, and tokens.
 */

import React from "react";
import { Box, Text } from "ink";
import type { SessionStatus } from "../types/agent.js";
import type { ThemeName } from "../types/theme.js";

interface StatusBarProps {
  status: SessionStatus | null;
  theme: ThemeName;
}

export function StatusBar({ status, theme }: StatusBarProps): React.ReactElement {
  if (!status) {
    return (
      <Box borderStyle="single" paddingX={1}>
        <Text dimColor>Qarin CLI v0.1.0 — No active session</Text>
      </Box>
    );
  }

  const contextPercent = status.contextUsage.percent;
  const contextColor = contextPercent > 80 ? "red" : contextPercent > 60 ? "yellow" : "green";
  const totalTokens = status.tokenUsage.totalTokens;

  return (
    <Box borderStyle="single" paddingX={1} justifyContent="space-between">
      <Box>
        <Text bold color="cyan">
          قرين{" "}
        </Text>
        <Text dimColor>
          {status.provider}/{status.model}
        </Text>
      </Box>

      <Box>
        <Text dimColor>🎨 {theme} </Text>
        <Text dimColor>│ </Text>
        <Text color={contextColor}>
          ctx: {contextPercent}%{" "}
        </Text>
        <Text dimColor>│ </Text>
        <Text dimColor>
          tokens: {totalTokens.toLocaleString()}{" "}
        </Text>
        <Text dimColor>│ </Text>
        <Text dimColor>
          msgs: {status.messageCount}
        </Text>
      </Box>
    </Box>
  );
}
