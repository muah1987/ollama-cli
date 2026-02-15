/**
 * Agent and session types for the qarin-cli core.
 */
/** Available built-in tools */
export const BUILT_IN_TOOLS = [
    {
        name: "file_read",
        description: "Read the contents of a file",
        parameters: {
            type: "object",
            properties: {
                path: { type: "string", description: "Path to file" },
            },
            required: ["path"],
        },
    },
    {
        name: "file_write",
        description: "Write content to a file",
        parameters: {
            type: "object",
            properties: {
                path: { type: "string", description: "Path to file" },
                content: { type: "string", description: "Content to write" },
            },
            required: ["path", "content"],
        },
    },
    {
        name: "file_edit",
        description: "Edit a range of lines in a file",
        parameters: {
            type: "object",
            properties: {
                path: { type: "string", description: "Path to file" },
                startLine: { type: "number", description: "Start line (1-based)" },
                endLine: { type: "number", description: "End line (1-based)" },
                newContent: { type: "string", description: "Replacement content" },
            },
            required: ["path", "startLine", "endLine", "newContent"],
        },
    },
    {
        name: "shell_exec",
        description: "Execute a shell command",
        parameters: {
            type: "object",
            properties: {
                command: { type: "string", description: "Command to execute" },
            },
            required: ["command"],
        },
    },
    {
        name: "grep_search",
        description: "Search for a pattern in files",
        parameters: {
            type: "object",
            properties: {
                pattern: { type: "string", description: "Regex pattern" },
                directory: { type: "string", description: "Directory to search" },
            },
            required: ["pattern"],
        },
    },
    {
        name: "web_fetch",
        description: "Fetch content from a URL",
        parameters: {
            type: "object",
            properties: {
                url: { type: "string", description: "URL to fetch" },
            },
            required: ["url"],
        },
    },
];
//# sourceMappingURL=agent.js.map