/**
 * Theme types for Arabic-themed progress indicators.
 */
/** Operation phases during agent execution */
export declare enum OperationPhase {
    ANALYZING = "analyzing",
    PLANNING = "planning",
    IMPLEMENTING = "implementing",
    TESTING = "testing",
    REVIEWING = "reviewing",
    COMPLETE = "complete",
    ERROR = "error"
}
/** A single themed stage with emoji and bilingual messages */
export interface ThemeStage {
    emoji: string;
    messageEn: string;
    messageAr?: string;
}
/** A complete theme mapping all phases to stages */
export type ThemeMap = Record<OperationPhase, ThemeStage>;
/** Available theme names */
export type ThemeName = "caravan" | "shisha" | "qahwa" | "scholarly";
/** Progress event emitted by the agent */
export interface ProgressEvent {
    phase: OperationPhase;
    details?: string;
    percent?: number;
}
/** Sub-agent wave progress */
export interface SubagentWaveEvent {
    wave: number;
    name: string;
    status: "started" | "completed" | "failed";
    details?: string;
}
//# sourceMappingURL=theme.d.ts.map