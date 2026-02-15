import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * User input area component for the chat interface.
 */
import { useState } from "react";
import { Box, Text, useInput } from "ink";
export function InputArea({ onSubmit, placeholder = "Type a message...", disabled = false, }) {
    const [input, setInput] = useState("");
    useInput((ch, key) => {
        if (disabled)
            return;
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
    });
    return (_jsxs(Box, { borderStyle: "single", paddingX: 1, children: [_jsx(Text, { color: "green", bold: true, children: "❯ " }), input ? (_jsx(Text, { children: input })) : (_jsx(Text, { dimColor: true, children: placeholder })), _jsx(Text, { color: "cyan", children: "\u2588" })] }));
}
//# sourceMappingURL=InputArea.js.map