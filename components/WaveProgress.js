import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Wave progress UI component.
 *
 * Shows which wave is active, which agents are running (spinner per agent),
 * merge status after each wave, and cumulative token count across waves.
 */
import React, { useState, useEffect } from "react";
import { Box, Text } from "ink";
const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const WAVE_LABELS = {
    0: { name: "Ingest", icon: "📥" },
    1: { name: "Analysis", icon: "🔍" },
    2: { name: "Plan/Val/Opt", icon: "📐" },
    3: { name: "Execution", icon: "⚡" },
    4: { name: "Finalize", icon: "✨" },
};
function AgentSpinner({ name, status }) {
    const [frame, setFrame] = useState(0);
    useEffect(() => {
        if (status !== "running")
            return;
        const timer = setInterval(() => {
            setFrame((prev) => (prev + 1) % SPINNER.length);
        }, 80);
        return () => clearInterval(timer);
    }, [status]);
    const icon = status === "done"
        ? "✓"
        : status === "error"
            ? "✗"
            : SPINNER[frame];
    const color = status === "done"
        ? "green"
        : status === "error"
            ? "red"
            : "cyan";
    return (_jsxs(Text, { children: [_jsxs(Text, { color: color, children: [icon, " "] }), _jsx(Text, { dimColor: status === "done", children: name })] }));
}
export function WaveProgress({ activeWave, agents, mergeStatus, totalTokens, totalCost, }) {
    if (activeWave == null)
        return null;
    const waveInfo = WAVE_LABELS[activeWave] ?? { name: `Wave ${activeWave}`, icon: "🔄" };
    return (_jsxs(Box, { flexDirection: "column", paddingX: 1, children: [_jsxs(Box, { children: [_jsxs(Text, { bold: true, color: "cyan", children: [waveInfo.icon, " Wave ", activeWave, ": ", waveInfo.name] }), totalTokens != null && (_jsxs(Text, { dimColor: true, children: [" | tokens: ", totalTokens.toLocaleString()] })), totalCost != null && totalCost > 0 && (_jsxs(Text, { dimColor: true, children: [" | $", totalCost.toFixed(4)] }))] }), agents && agents.length > 0 && (_jsx(Box, { marginLeft: 2, gap: 2, children: agents.map((agent) => (_jsx(AgentSpinner, { name: agent.name, status: agent.status }, agent.name))) })), mergeStatus && (_jsxs(Box, { marginLeft: 2, children: [_jsx(Text, { color: "green", children: "\u2713 " }), _jsx(Text, { dimColor: true, children: mergeStatus })] }))] }));
}
//# sourceMappingURL=WaveProgress.js.map
