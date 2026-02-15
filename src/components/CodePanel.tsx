/**
 * Code panel component for displaying syntax-highlighted code blocks.
 */

import React from "react";
import { Box, Text } from "ink";

interface CodePanelProps {
  code: string;
  language?: string;
  filename?: string;
  showLineNumbers?: boolean;
}

export function CodePanel({
  code,
  language,
  filename,
  showLineNumbers = true,
}: CodePanelProps): React.ReactElement {
  const lines = code.split("\n");

  return (
    <Box flexDirection="column" borderStyle="single" paddingX={1}>
      {(filename || language) && (
        <Box marginBottom={1}>
          {filename && (
            <Text bold color="cyan">
              📄 {filename}
            </Text>
          )}
          {language && (
            <Text dimColor> [{language}]</Text>
          )}
        </Box>
      )}

      <Box flexDirection="column">
        {lines.map((line, i) => (
          <Box key={i}>
            {showLineNumbers && (
              <Text dimColor>{String(i + 1).padStart(4)} │ </Text>
            )}
            <Text>{line}</Text>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
