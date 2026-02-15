/**
 * Status bar component showing session info, model, theme, and tokens.
 */
import React from "react";
import type { SessionStatus } from "../types/agent.js";
import type { ThemeName } from "../types/theme.js";
interface StatusBarProps {
    status: SessionStatus | null;
    theme: ThemeName;
}
export declare function StatusBar({ status, theme }: StatusBarProps): React.ReactElement;
export {};
//# sourceMappingURL=StatusBar.d.ts.map