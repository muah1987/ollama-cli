import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { Box, Text } from "ink";
export function DiffViewer({ filename, lines }) {
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "single", paddingX: 1, children: [_jsxs(Text, { bold: true, color: "white", children: ["\uD83D\uDCC4 ", filename] }), _jsx(Box, { flexDirection: "column", marginTop: 1, children: lines.map((line, i) => {
                    const color = line.type === "add" ? "green" : line.type === "remove" ? "red" : "white";
                    const prefix = line.type === "add" ? "+" : line.type === "remove" ? "-" : " ";
                    return (_jsxs(Box, { children: [line.lineNumber !== undefined && (_jsxs(Text, { dimColor: true, children: [String(line.lineNumber).padStart(4), " "] })), _jsxs(Text, { color: color, children: [prefix, " ", line.content] })] }, i));
                }) })] }));
}
//# sourceMappingURL=DiffViewer.js.map