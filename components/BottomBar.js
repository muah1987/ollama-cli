import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * BOTTOM region -- cwd, run_uuid, model/status, live metrics.
 *
 * Updates in real time as waves complete, showing tokens,
 * timings, cost estimate, and exit status.
 */
import { Box, Text } from "ink";
export function BottomBar({ runUuid, model, provider, cwd, tokenDisplay, waveStatus, costEstimate, exitStatus, }) {
    const shortUuid = runUuid ? runUuid.slice(0, 8) : "--------";
    const shortCwd = cwd
        ? cwd.replace(process.env.HOME ?? "", "~")
        : process.cwd().replace(process.env.HOME ?? "", "~");
    const statusColor = exitStatus === "ok"
        ? "green"
        : exitStatus === "error"
            ? "red"
            : "yellow";
    return (_jsxs(Box, { borderStyle: "single", paddingX: 1, justifyContent: "space-between", children: [_jsxs(Box, { children: [_jsx(Text, { dimColor: true, children: shortCwd }), _jsx(Text, { dimColor: true, children: " | " }), _jsxs(Text, { dimColor: true, children: ["id:", shortUuid] })] }), _jsxs(Box, { children: [_jsxs(Text, { dimColor: true, children: [provider, "/", model] }), waveStatus && (_jsxs(Text, { color: "cyan", children: [" | W", waveStatus] })), tokenDisplay && (_jsxs(Text, { dimColor: true, children: [" | ", tokenDisplay] })), costEstimate != null && costEstimate > 0 && (_jsxs(Text, { dimColor: true, children: [" | $", costEstimate.toFixed(4)] })), _jsx(Text, { color: statusColor, children: exitStatus === "ok"
                            ? " | ok"
                            : exitStatus === "error"
                                ? " | err"
                                : " | ..." })] })] }));
}
//# sourceMappingURL=BottomBar.js.map
