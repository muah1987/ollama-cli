import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from "ink";
export function StatusBar({ status, theme }) {
    if (!status) {
        return (_jsx(Box, { borderStyle: "single", paddingX: 1, children: _jsx(Text, { dimColor: true, children: "Qarin CLI v0.1.0 \u2014 No active session" }) }));
    }
    const contextPercent = status.contextUsage.percent;
    const contextColor = contextPercent > 80 ? "red" : contextPercent > 60 ? "yellow" : "green";
    const totalTokens = status.tokenUsage.totalTokens;
    return (_jsxs(Box, { borderStyle: "single", paddingX: 1, justifyContent: "space-between", children: [_jsxs(Box, { children: [_jsxs(Text, { bold: true, color: "cyan", children: ["\u0642\u0631\u064A\u0646", " "] }), _jsxs(Text, { dimColor: true, children: [status.provider, "/", status.model] })] }), _jsxs(Box, { children: [_jsxs(Text, { dimColor: true, children: ["\uD83C\uDFA8 ", theme, " "] }), _jsx(Text, { dimColor: true, children: "\u2502 " }), _jsxs(Text, { color: contextColor, children: ["ctx: ", contextPercent, "%", " "] }), _jsx(Text, { dimColor: true, children: "\u2502 " }), _jsxs(Text, { dimColor: true, children: ["tokens: ", totalTokens.toLocaleString(), " "] }), _jsx(Text, { dimColor: true, children: "\u2502 " }), _jsxs(Text, { dimColor: true, children: ["msgs: ", status.messageCount] })] })] }));
}
//# sourceMappingURL=StatusBar.js.map