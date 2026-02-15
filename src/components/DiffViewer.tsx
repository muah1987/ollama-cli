/**
 * Diff viewer component for displaying code changes.
 */

import React from "react";
import { Box, Text } from "ink";

interface DiffLine {
  type: "add" | "remove" | "context";
  content: string;
  lineNumber?: number;
}

interface DiffViewerProps {
  filename: string;
  lines: DiffLine[];
}

export function DiffViewer({ filename, lines }: DiffViewerProps): React.ReactElement {
  return (
    <Box flexDirection="column" borderStyle="single" paddingX={1}>
      <Text bold color="white">
        📄 {filename}
      </Text>
      <Box flexDirection="column" marginTop={1}>
        {lines.map((line, i) => {
          const color = line.type === "add" ? "green" : line.type === "remove" ? "red" : "white";
          const prefix = line.type === "add" ? "+" : line.type === "remove" ? "-" : " ";

          return (
            <Box key={i}>
              {line.lineNumber !== undefined && (
                <Text dimColor>{String(line.lineNumber).padStart(4)} </Text>
              )}
              <Text color={color}>
                {prefix} {line.content}
              </Text>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
