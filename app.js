import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Main Ink application component.
 *
 * Renders the full chat interface with TOP/MID/BOTTOM region layout:
 * - TOP: ASCII banner, session info, warnings
 * - MID: Chat messages, streaming output, wave progress, themed progress
 * - BOTTOM: cwd, run_uuid, model, live metrics
 */
import React, { useState, useCallback } from "react";
import { Box, Text, useApp } from "ink";
import { useAgent } from "./hooks/useAgent.js";
import { useTheme } from "./hooks/useTheme.js";
import { TopBanner } from "./components/TopBanner.js";
import { BottomBar } from "./components/BottomBar.js";
import { ChatView } from "./components/ChatView.js";
import { WaveProgress } from "./components/WaveProgress.js";
import { ProgressTheme } from "./components/ProgressTheme.js";
import { InputArea } from "./components/InputArea.js";
import { Session } from "./core/session.js";
/** Generate a run UUID for this invocation */
const RUN_UUID = crypto.randomUUID();
/** Load the latest session with full context from .qarin/sessions/ */
async function loadLatestSession() {
    const { readdir, readFile } = await import("node:fs/promises");
    const { join, resolve } = await import("node:path");
    const sessionsDir = resolve(".qarin/sessions");
    try {
        const files = await readdir(sessionsDir);
        const jsonFiles = files.filter((f) => f.endsWith(".json")).sort().reverse();
        if (jsonFiles.length === 0)
            return { messages: [], sessionData: null };
        const content = await readFile(join(sessionsDir, jsonFiles[0]), "utf-8");
        const data = JSON.parse(content);
        return {
            messages: data.contextManager?.messages ?? [],
            sessionData: data,
        };
    }
    catch {
        return { messages: [], sessionData: null };
    }
}
export default function QarinApp({ task, options }) {
    const { exit } = useApp();
    const { theme, nextTheme } = useTheme(options.theme);
    const { phase, details, isProcessing, streamOutput, status, intent, tokenDisplay, error, sendMessage, endSession, getAgent, } = useAgent(options);
    const [messages, setMessages] = useState([]);
    const [resumeLoaded, setResumeLoaded] = useState(false);
    // Wave progress state
    const [activeWave, setActiveWave] = useState(null);
    const [waveAgents, setWaveAgents] = useState([]);
    const [mergeStatus, setMergeStatus] = useState(null);
    const [exitStatus, setExitStatus] = useState("running");
    // Handle --resume: load the latest session on mount
    React.useEffect(() => {
        if (options.resume && !resumeLoaded) {
            setResumeLoaded(true);
            loadLatestSession().then(({ messages: msgs, sessionData }) => {
                if (msgs.length > 0) {
                    setMessages(msgs);
                    if (sessionData) {
                        const info = [
                            `Resumed session ${sessionData.sessionId}`,
                            `Model: ${sessionData.provider}/${sessionData.model}`,
                            `Messages: ${sessionData.messageCount}`,
                            sessionData.tokenCounter ? `Tokens: ${sessionData.tokenCounter.totalTokens?.toLocaleString() ?? 0}` : null,
                        ].filter(Boolean).join(" | ");
                        setMessages((prev) => [{ role: "system", content: info }, ...prev]);
                    }
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
            setExitStatus("ok");
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
        // /memory commands
        if (text.startsWith("/memory")) {
            const agent = getAgent();
            if (!agent) {
                setMessages((prev) => [...prev, { role: "system", content: "No active agent." }]);
                return;
            }
            const memory = agent.getMemory();
            const parts = text.split(/\s+/);
            const subCmd = parts[1] ?? "list";
            if (subCmd === "list") {
                const entries = await memory.list();
                const display = entries.length > 0
                    ? entries.map((e) => `[${e.id}] ${e.content} (${e.tags.join(", ") || "no tags"})`).join("\n")
                    : "No memories stored.";
                setMessages((prev) => [...prev, { role: "system", content: `Memory (${entries.length} entries):\n${display}` }]);
            }
            else if (subCmd === "search") {
                const query = parts.slice(2).join(" ");
                if (!query) {
                    setMessages((prev) => [...prev, { role: "system", content: "Usage: /memory search <query>" }]);
                    return;
                }
                const results = await memory.search(query);
                const display = results.length > 0
                    ? results.map((r) => `[${(r.similarity * 100).toFixed(0)}%] ${r.content}`).join("\n")
                    : "No matching memories.";
                setMessages((prev) => [...prev, { role: "system", content: `Search results:\n${display}` }]);
            }
            else if (subCmd === "add") {
                const content = parts.slice(2).join(" ");
                if (!content) {
                    setMessages((prev) => [...prev, { role: "system", content: "Usage: /memory add <fact>" }]);
                    return;
                }
                const id = await memory.store(content, { source: "user" });
                setMessages((prev) => [...prev, { role: "system", content: `Stored memory ${id}` }]);
            }
            else if (subCmd === "clear") {
                const count = await memory.clear();
                setMessages((prev) => [...prev, { role: "system", content: `Cleared ${count} memories.` }]);
            }
            else {
                setMessages((prev) => [...prev, { role: "system", content: "Usage: /memory [list|search <query>|add <fact>|clear]" }]);
            }
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
        // Reset wave state
        setActiveWave(null);
        setWaveAgents([]);
        setMergeStatus(null);
        // Add user message to display
        setMessages((prev) => [...prev, { role: "user", content: text }]);
        try {
            // Send to agent
            await sendMessage(text);
            setExitStatus("ok");
        }
        catch {
            setExitStatus("error");
        }
    }, [sendMessage, endSession, nextTheme, exit, status]);
    // If a task was passed as an argument, execute it immediately
    React.useEffect(() => {
        if (task) {
            handleSubmit(task).catch((err) => {
                const message = err instanceof Error ? err.message : String(err);
                setMessages((prev) => [...prev, { role: "system", content: `Error: ${message}` }]);
                setExitStatus("error");
            });
        }
    }, []);
    // Append assistant responses to messages
    React.useEffect(() => {
        if (streamOutput && !isProcessing) {
            setMessages((prev) => [...prev, { role: "assistant", content: streamOutput }]);
        }
    }, [isProcessing, streamOutput]);
    const costEstimate = status
        ? (status.tokenUsage.totalTokens / 1_000_000) * 15
        : 0;
    return (_jsxs(Box, { flexDirection: "column", height: "100%", children: [
        // ─── TOP REGION ─────────────────────────────────
        _jsx(TopBanner, {
            sessionId: status?.sessionId ?? RUN_UUID,
            model: options.model,
            provider: options.provider,
            chainMode: options.chain,
        }),
        // ─── MID REGION ─────────────────────────────────
        _jsxs(Box, { flexDirection: "column", flexGrow: 1, paddingX: 1, marginY: 1, children: [
            _jsx(ChatView, { messages: messages }),
            isProcessing && streamOutput && (
                _jsx(Box, { marginLeft: 2, children: _jsx(Text, { color: "cyan", children: streamOutput }) })
            ),
        ] }),
        // Intent badge
        intent && intent.confidence > 0 && (
            _jsx(Box, { paddingX: 1, children: _jsxs(Text, { dimColor: true, children: [
                "Intent: ", intent.agentType, " (",
                Math.round(intent.confidence * 100), "%)",
                intent.matchedPatterns.length > 0 &&
                    ` [${intent.matchedPatterns.slice(0, 3).join(", ")}]`,
            ] }) })
        ),
        // Wave progress (chain mode)
        isProcessing && activeWave != null && (
            _jsx(WaveProgress, {
                activeWave: activeWave,
                agents: waveAgents,
                mergeStatus: mergeStatus,
                totalTokens: status?.tokenUsage.totalTokens,
                totalCost: costEstimate,
            })
        ),
        // Themed progress (standard mode)
        isProcessing && activeWave == null && (
            _jsx(Box, { paddingX: 1, children: _jsx(ProgressTheme, { theme: theme, phase: phase, details: details }) })
        ),
        // Token display
        tokenDisplay && !isProcessing && (
            _jsx(Box, { paddingX: 1, children: _jsx(Text, { dimColor: true, children: tokenDisplay }) })
        ),
        // Error display
        error && (
            _jsx(Box, { paddingX: 1, children: _jsxs(Text, { color: "red", children: ["Error: ", error.message] }) })
        ),
        // Input area
        _jsx(InputArea, {
            onSubmit: handleSubmit,
            placeholder: "Type a message... (/quit, /theme, /status, /save, /memory)",
            disabled: isProcessing,
        }),
        // ─── BOTTOM REGION ──────────────────────────────
        _jsx(BottomBar, {
            runUuid: RUN_UUID,
            model: options.model,
            provider: options.provider,
            cwd: process.cwd(),
            tokenDisplay: tokenDisplay || undefined,
            waveStatus: activeWave != null ? String(activeWave) : undefined,
            costEstimate: costEstimate,
            exitStatus: isProcessing ? "running" : exitStatus,
        }),
    ] }));
}
//# sourceMappingURL=app.js.map
