/**
 * Themed progress indicator component.
 *
 * Displays operation progress with Arabic-themed messages,
 * emoji, and bilingual text.
 */
import React from "react";
import type { OperationPhase, ThemeName } from "../types/theme.js";
interface ProgressThemeProps {
    theme: ThemeName;
    phase: OperationPhase;
    details?: string;
}
export declare function ProgressTheme({ theme, phase, details }: ProgressThemeProps): React.ReactElement;
export {};
//# sourceMappingURL=ProgressTheme.d.ts.map