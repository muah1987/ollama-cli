/**
 * Diff viewer component for displaying code changes.
 */
import React from "react";
interface DiffLine {
    type: "add" | "remove" | "context";
    content: string;
    lineNumber?: number;
}
interface DiffViewerProps {
    filename: string;
    lines: DiffLine[];
}
export declare function DiffViewer({ filename, lines }: DiffViewerProps): React.ReactElement;
export {};
//# sourceMappingURL=DiffViewer.d.ts.map