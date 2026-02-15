import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { Box, Text } from "ink";
/** Role display configuration */
const ROLE_STYLES = {
    user: { label: "You", color: "green" },
    assistant: { label: "Qarin", color: "cyan" },
    system: { label: "System", color: "yellow" },
    tool: { label: "Tool", color: "magenta" },
};
function ChatMessage({ message }) {
    const style = ROLE_STYLES[message.role] ?? { label: message.role, color: "white" };
    return (_jsxs(Box, { flexDirection: "column", marginBottom: 1, children: [_jsxs(Text, { bold: true, color: style.color, children: [style.label, ":"] }), _jsx(Box, { marginLeft: 2, children: _jsx(Text, { wrap: "wrap", children: message.content }) })] }));
}
export function ChatView({ messages }) {
    const visibleMessages = messages.filter((m) => m.role !== "system");
    if (visibleMessages.length === 0) {
        return (_jsx(Box, { children: _jsx(Text, { dimColor: true, children: "No messages yet. Type a message to get started." }) }));
    }
    return (_jsx(Box, { flexDirection: "column", children: visibleMessages.map((msg, i) => (_jsx(ChatMessage, { message: msg }, i))) }));
}
//# sourceMappingURL=ChatView.js.map