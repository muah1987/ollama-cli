import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Main Ink application component.
 *
 * Renders the full chat interface with status bar, messages,
 * themed progress, intent badge, token display, and input area.
 */
import React, { useState, useCallback } from "react";
import { Box, Text, useApp } from "ink";
import { useAgent } from "./hooks/useAgent.js";
import { useTheme } from "./hooks/useTheme.js";
import { StatusBar } from "./components/StatusBar.js";
import { ChatView } from "./components/ChatView.js";
import { ProgressTheme } from "./components/ProgressTheme.js";
import { InputArea } from "./components/InputArea.js";
import { Session } from "./core/session.js";
/** Load the latest session's messages from .qarin/sessions/ */
async function loadLatestSession() {
    const { readdir, readFile } = await import("node:fs/promises");
    const { join, resolve } = await import("node:path");
    const sessionsDir = resolve(".qarin/sessions");
    try {
        const files = await readdir(sessionsDir);
        const jsonFiles = files.filter((f) => f.endsWith(".json")).sort().reverse();
        if (jsonFiles.length === 0)
            return [];
        const content = await readFile(join(sessionsDir, jsonFiles[0]), "utf-8");
        const data = JSON.parse(content);
        return data.contextManager?.messages ?? [];
    }
    catch {
        return [];
    }
}
export default function QarinApp({ task, options }) {
    const { exit } = useApp();
    const { theme, nextTheme } = useTheme(options.theme);
    const { phase, details, isProcessing, streamOutput, status, intent, tokenDisplay, error, sendMessage, endSession, } = useAgent(options);
    const [messages, setMessages] = useState([]);
    const [resumeLoaded, setResumeLoaded] = useState(false);
    // Handle --resume: load the latest session on mount
    React.useEffect(() => {
        if (options.resume && !resumeLoaded) {
            setResumeLoaded(true);
            loadLatestSession().then((msgs) => {
                if (msgs.length > 0) {
                    setMessages(msgs);
                }
                else {
                    setMessages([{ role: "system", content: "No previous session found." }]);
                }
            }).catch(() => {
                setMessages([{ role: "system", content: "Failed to load previous session." }]);
            });
        }
    }, []);
    const handleSubmit = useCallback(async (text) => {
        if (text === "/quit" || text === "/exit") {
            await endSession();
            exit();
            return;
        }
        if (text === "/save") {
            const session = new Session({
                model: options.model,
                provider: options.provider,
            });
            const savePath = await session.save();
            setMessages((prev) => [...prev, { role: "system", content: `Session saved to ${savePath}` }]);
            return;
        }
        if (text === "/theme") {
            nextTheme();
            return;
        }
        if (text === "/status") {
            const timestamp = new Date().toLocaleString();
            const statusMsg = status
                ? `Status snapshot at ${timestamp} (not updated automatically)\nSession: ${status.sessionId}\nModel: ${status.provider}/${status.model}\nMessages: ${status.messageCount}\nTokens: ${status.tokenUsage.totalTokens.toLocaleString()}\nContext: ${status.contextUsage.percent}%`
                : "No active session";
            setMessages((prev) => [...prev, { role: "system", content: statusMsg }]);
            return;
        }
        // Add user message to display
        setMessages((prev) => [...prev, { role: "user", content: text }]);
        // Send to agent
        await sendMessage(text);
    }, [sendMessage, endSession, nextTheme, exit, status]);
    // If a task was passed as an argument, execute it immediately
    React.useEffect(() => {
        if (task) {
            handleSubmit(task).catch((err) => {
                // Display error if initial task fails
                const message = err instanceof Error ? err.message : String(err);
                setMessages((prev) => [...prev, { role: "system", content: `Error: ${message}` }]);
            });
        }
    }, []);
    // Append assistant responses to messages
    React.useEffect(() => {
        if (streamOutput && !isProcessing) {
            setMessages((prev) => [...prev, { role: "assistant", content: streamOutput }]);
        }
    }, [isProcessing, streamOutput]);
    return (_jsxs(Box, { flexDirection: "column", height: "100%", children: [_jsx(StatusBar, { status: status, theme: theme }), _jsxs(Box, { flexDirection: "column", flexGrow: 1, paddingX: 1, marginY: 1, children: [_jsx(ChatView, { messages: messages }), isProcessing && streamOutput && (_jsx(Box, { marginLeft: 2, children: _jsx(Text, { color: "cyan", children: streamOutput }) }))] }), intent && intent.confidence > 0 && (_jsx(Box, { paddingX: 1, children: _jsxs(Text, { dimColor: true, children: ["Intent: ", intent.agentType, " (", Math.round(intent.confidence * 100), "%)", intent.matchedPatterns.length > 0 &&
                            ` [${intent.matchedPatterns.slice(0, 3).join(", ")}]`] }) })), isProcessing && (_jsx(Box, { paddingX: 1, children: _jsx(ProgressTheme, { theme: theme, phase: phase, details: details }) })), tokenDisplay && !isProcessing && (_jsx(Box, { paddingX: 1, children: _jsx(Text, { dimColor: true, children: tokenDisplay }) })), error && (_jsx(Box, { paddingX: 1, children: _jsxs(Text, { color: "red", children: ["Error: ", error.message] }) })), _jsx(InputArea, { onSubmit: handleSubmit, placeholder: "Type a message... (/quit, /theme, /status, /save)", disabled: isProcessing })] }));
}
//# sourceMappingURL=app.js.map