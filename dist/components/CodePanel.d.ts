/**
 * Code panel component for displaying syntax-highlighted code blocks.
 */
import React from "react";
interface CodePanelProps {
    code: string;
    language?: string;
    filename?: string;
    showLineNumbers?: boolean;
}
export declare function CodePanel({ code, language, filename, showLineNumbers, }: CodePanelProps): React.ReactElement;
export {};
//# sourceMappingURL=CodePanel.d.ts.map