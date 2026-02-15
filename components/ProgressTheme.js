import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
/**
 * Themed progress indicator component.
 *
 * Displays operation progress with Arabic-themed messages,
 * emoji, and bilingual text.
 */
import React from "react";
import { Box, Text } from "ink";
import { getThemeStage } from "../themes/index.js";
/** Animated spinner frames */
const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
export function ProgressTheme({ theme, phase, details }) {
    const [frame, setFrame] = React.useState(0);
    const stage = getThemeStage(theme, phase);
    const isComplete = phase === "complete" || phase === "error";
    React.useEffect(() => {
        if (isComplete)
            return;
        const timer = setInterval(() => {
            setFrame((prev) => (prev + 1) % SPINNER_FRAMES.length);
        }, 80);
        return () => clearInterval(timer);
    }, [isComplete]);
    return (_jsxs(Box, { children: [!isComplete && _jsxs(Text, { color: "cyan", children: [SPINNER_FRAMES[frame], " "] }), _jsxs(Text, { children: [stage.emoji, " "] }), _jsx(Text, { color: "cyan", children: stage.messageEn }), stage.messageAr && _jsxs(Text, { dimColor: true, children: [" (", stage.messageAr, ")"] }), details && _jsxs(Text, { dimColor: true, children: [" \u2192 ", details] })] }));
}
//# sourceMappingURL=ProgressTheme.js.map