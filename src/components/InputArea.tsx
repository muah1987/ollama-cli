/**
 * User input area component for the chat interface.
 */

import React, { useState } from "react";
import { Box, Text, useInput } from "ink";

interface InputAreaProps {
  onSubmit: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function InputArea({
  onSubmit,
  placeholder = "Type a message...",
  disabled = false,
}: InputAreaProps): React.ReactElement {
  const [input, setInput] = useState("");

  useInput(
    (ch, key) => {
      if (disabled) return;

      if (key.return) {
        if (input.trim()) {
          onSubmit(input.trim());
          setInput("");
        }
        return;
      }

      if (key.backspace || key.delete) {
        setInput((prev) => prev.slice(0, -1));
        return;
      }

      if (ch && !key.ctrl && !key.meta) {
        setInput((prev) => prev + ch);
      }
    },
  );

  return (
    <Box borderStyle="single" paddingX={1}>
      <Text color="green" bold>
        {"❯ "}
      </Text>
      {input ? (
        <Text>{input}</Text>
      ) : (
        <Text dimColor>{placeholder}</Text>
      )}
      <Text color="cyan">█</Text>
    </Box>
  );
}
