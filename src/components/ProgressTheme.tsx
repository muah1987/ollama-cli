/**
 * Themed progress indicator component.
 *
 * Displays operation progress with Arabic-themed messages,
 * emoji, and bilingual text.
 */

import React from "react";
import { Box, Text } from "ink";
import type { OperationPhase, ThemeName, ThemeStage } from "../types/theme.js";
import { getThemeStage } from "../themes/index.js";

interface ProgressThemeProps {
  theme: ThemeName;
  phase: OperationPhase;
  details?: string;
}

/** Animated spinner frames */
const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

export function ProgressTheme({ theme, phase, details }: ProgressThemeProps): React.ReactElement {
  const [frame, setFrame] = React.useState(0);
  const stage: ThemeStage = getThemeStage(theme, phase);
  const isComplete = phase === "complete" || phase === "error";

  React.useEffect(() => {
    if (isComplete) return;

    const timer = setInterval(() => {
      setFrame((prev) => (prev + 1) % SPINNER_FRAMES.length);
    }, 80);

    return () => clearInterval(timer);
  }, [isComplete]);

  return (
    <Box>
      {!isComplete && <Text color="cyan">{SPINNER_FRAMES[frame]} </Text>}
      <Text>{stage.emoji} </Text>
      <Text color="cyan">{stage.messageEn}</Text>
      {stage.messageAr && <Text dimColor> ({stage.messageAr})</Text>}
      {details && <Text dimColor> → {details}</Text>}
    </Box>
  );
}
