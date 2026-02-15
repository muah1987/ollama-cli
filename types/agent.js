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
    {
        name: "git_diff",
        description: "Show git diff (staged and/or unstaged changes)",
        parameters: {
            type: "object",
            properties: {
                staged: { type: "boolean", description: "Show only staged changes" },
                path: { type: "string", description: "Limit diff to a specific file" },
            },
        },
    },
    {
        name: "git_commit",
        description: "Stage files and commit with a message",
        parameters: {
            type: "object",
            properties: {
                message: { type: "string", description: "Commit message" },
                files: {
                    type: "array",
                    items: { type: "string" },
                    description: "Files to stage (defaults to all)",
                },
            },
            required: ["message"],
        },
    },
    {
        name: "code_search",
        description: "Search code for a pattern using ripgrep or grep",
        parameters: {
            type: "object",
            properties: {
                pattern: { type: "string", description: "Search pattern (regex)" },
                directory: { type: "string", description: "Directory to search" },
                fileType: { type: "string", description: "File type filter (e.g. js, py)" },
            },
            required: ["pattern"],
        },
    },
    {
        name: "test_run",
        description: "Run the project test suite",
        parameters: {
            type: "object",
            properties: {
                command: { type: "string", description: "Custom test command (defaults to npm test)" },
            },
        },
    },
    {
        name: "lint_check",
        description: "Run linter and return diagnostics",
        parameters: {
            type: "object",
            properties: {
                command: { type: "string", description: "Custom lint command (defaults to eslint)" },
            },
        },
    },
];
//# sourceMappingURL=agent.js.map