import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { Box, Text } from "ink";
export function CodePanel({ code, language, filename, showLineNumbers = true, }) {
    const lines = code.split("\n");
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "single", paddingX: 1, children: [(filename || language) && (_jsxs(Box, { marginBottom: 1, children: [filename && (_jsxs(Text, { bold: true, color: "cyan", children: ["\uD83D\uDCC4 ", filename] })), language && (_jsxs(Text, { dimColor: true, children: [" [", language, "]"] }))] })), _jsx(Box, { flexDirection: "column", children: lines.map((line, i) => (_jsxs(Box, { children: [showLineNumbers && (_jsxs(Text, { dimColor: true, children: [String(i + 1).padStart(4), " \u2502 "] })), _jsx(Text, { children: line })] }, i))) })] }));
}
//# sourceMappingURL=CodePanel.js.map