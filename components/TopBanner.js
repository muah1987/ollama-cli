import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * TOP region -- ASCII banner, startup info, and warnings.
 *
 * Displays the Qarin banner with session metadata and any
 * warnings from .qarin/warnings if present.
 */
import React, { useState, useEffect } from "react";
import { Box, Text } from "ink";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
const BANNER = [
    "   ___            _       ",
    "  / _ \\__ _ _ __(_)_ __  ",
    " / /_)/ _` | '__| | '_ \\ ",
    "/ ___/ (_| | |  | | | | |",
    "\\/    \\__,_|_|  |_|_| |_|",
];
const BANNER_AR = "قرين — مساعد البرمجة";
export function TopBanner({ sessionId, model, provider, chainMode }) {
    const [warnings, setWarnings] = useState([]);
    useEffect(() => {
        const warningsPath = resolve(process.env.QARIN_PROJECT_DIR ?? process.cwd(), ".qarin", "warnings");
        readFile(warningsPath, "utf-8")
            .then((content) => {
            const lines = content.trim().split("\n").filter(Boolean);
            setWarnings(lines);
        })
            .catch(() => { });
    }, []);
    const shortId = sessionId ? sessionId.slice(0, 8) : "--------";
    return (_jsxs(Box, { flexDirection: "column", paddingX: 1, children: [_jsx(Box, { flexDirection: "column", children: BANNER.map((line, i) => (_jsx(Text, { color: "cyan", bold: i === 0, children: line }, i))) }), _jsxs(Box, { marginTop: 0, children: [_jsx(Text, { dimColor: true, children: BANNER_AR }), _jsxs(Text, { dimColor: true, children: [" | v0.4.0 | ", provider, "/", model] }), chainMode && _jsx(Text, { color: "yellow", children: " | chain" }), _jsxs(Text, { dimColor: true, children: [" | ", shortId] })] }), warnings.length > 0 && (_jsx(Box, { flexDirection: "column", marginTop: 1, children: warnings.map((w, i) => (_jsxs(Text, { color: "yellow", children: ["\u26A0 ", w] }, i))) }))] }));
}
//# sourceMappingURL=TopBanner.js.map
