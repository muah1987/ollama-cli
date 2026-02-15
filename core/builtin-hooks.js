/**
 * Built-in hook library and hook composition system.
 *
 * Provides:
 * - auto-lint: Run linter on written files (PostToolUse + file_write)
 * - auto-test: Run tests when test files modified (PostToolUse + file_write)
 * - commit-guard: Block dangerous git commands (PreToolUse + shell_exec)
 * - token-alert: Warn when cost exceeds threshold (Notification)
 *
 * Hook permissions gate:
 * - PreToolUse hooks can return { allow: false, reason: "..." }
 * - Configurable allowlists per tool
 * - Audit log to .qarin/audit.log
 */
import { appendFile, mkdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { isDestructiveCommand } from "./tools.js";
/** Dangerous patterns that commit-guard blocks */
const BLOCKED_COMMANDS = [
    /\bgit\s+push\s+--force\b/,
    /\bgit\s+push\s+-f\b/,
    /\brm\s+-rf\s+\/(?!\S)/,
    /\brm\s+-rf\s+~\//,
    /\bdrop\s+database\b/i,
    /\bformat\s+[a-z]:/i,
    /\bmkfs\./,
    /\bdd\s+if=.*of=\/dev/,
];
/**
 * Audit logger -- writes to .qarin/audit.log
 */
async function auditLog(entry) {
    const logPath = resolve(process.env.QARIN_PROJECT_DIR ?? process.cwd(), ".qarin", "audit.log");
    const timestamp = new Date().toISOString();
    const line = `${timestamp} | ${entry.event} | ${entry.tool ?? "-"} | ${entry.action} | ${entry.details ?? ""}\n`;
    try {
        await mkdir(dirname(logPath), { recursive: true });
        await appendFile(logPath, line);
    }
    catch {
        // Best effort
    }
}
/**
 * Commit guard: block dangerous git/shell commands.
 *
 * Returns { allow, reason } for PreToolUse hooks.
 */
export function commitGuard(payload) {
    const command = payload.arguments?.command ?? "";
    for (const pattern of BLOCKED_COMMANDS) {
        if (pattern.test(command)) {
            return {
                allow: false,
                reason: `Blocked by commit-guard: "${command}" matches dangerous pattern`,
            };
        }
    }
    if (isDestructiveCommand(command)) {
        return {
            allow: false,
            reason: `Blocked by commit-guard: "${command}" is a destructive command. Use --force to override.`,
        };
    }
    return { allow: true };
}
/**
 * Auto-lint: check if a written file should be linted.
 */
export function shouldAutoLint(payload) {
    const toolName = payload.tool_name ?? payload.toolName ?? "";
    if (toolName !== "file_write" && toolName !== "file_edit")
        return false;
    const path = payload.result?.output ?? payload.arguments?.path ?? "";
    const lintableExtensions = [".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs", ".py", ".rb"];
    return lintableExtensions.some((ext) => path.endsWith(ext));
}
/**
 * Auto-test: check if a modified file is a test file.
 */
export function shouldAutoTest(payload) {
    const toolName = payload.tool_name ?? payload.toolName ?? "";
    if (toolName !== "file_write" && toolName !== "file_edit")
        return false;
    const path = payload.arguments?.path ?? "";
    const testPatterns = [".test.", ".spec.", "__tests__", "test_", "_test."];
    return testPatterns.some((p) => path.includes(p));
}
/**
 * Token alert: check if cost exceeds threshold.
 */
export function tokenAlert(totalTokens, threshold = 100_000) {
    if (totalTokens > threshold) {
        return {
            alert: true,
            message: `Token usage (${totalTokens.toLocaleString()}) exceeds threshold (${threshold.toLocaleString()})`,
        };
    }
    return { alert: false };
}
/**
 * Hook permissions gate.
 *
 * Checks if a tool call is allowed based on allowlists and
 * PreToolUse hook results.
 */
export class HookPermissions {
    allowlists;
    denyPatterns;
    constructor(config) {
        this.allowlists = config?.allowlists ?? {};
        this.denyPatterns = config?.denyPatterns ?? {};
    }
    /**
     * Check if a tool call is allowed.
     *
     * @returns { allowed, reason }
     */
    check(toolName, args) {
        // Check deny patterns first
        const denyList = this.denyPatterns[toolName];
        if (denyList) {
            for (const pattern of denyList) {
                const regex = new RegExp(pattern);
                const argsStr = JSON.stringify(args);
                if (regex.test(argsStr)) {
                    return {
                        allowed: false,
                        reason: `Denied by pattern: ${pattern}`,
                    };
                }
            }
        }
        // Check allowlists
        const allowlist = this.allowlists[toolName];
        if (allowlist && allowlist.length > 0) {
            // If there's an allowlist, only listed args are allowed
            const argsStr = JSON.stringify(args);
            const isAllowed = allowlist.some((pattern) => new RegExp(pattern).test(argsStr));
            if (!isAllowed) {
                return {
                    allowed: false,
                    reason: `Not in allowlist for ${toolName}`,
                };
            }
        }
        // Check built-in guards for shell_exec
        if (toolName === "shell_exec") {
            const guard = commitGuard({ arguments: args });
            if (!guard.allow) {
                return { allowed: false, reason: guard.reason };
            }
        }
        return { allowed: true };
    }
    /** Log a permission check to audit trail */
    async audit(toolName, args, result) {
        await auditLog({
            event: "permission_check",
            tool: toolName,
            action: result.allowed ? "ALLOWED" : "DENIED",
            details: result.reason ?? "",
        });
    }
}
/**
 * Hook composition: chain hooks where output flows to next input.
 */
export class HookChain {
    hooks = [];
    /** Add a hook to the chain */
    add(name, fn, options) {
        this.hooks.push({ name, fn, condition: options?.condition });
    }
    /**
     * Execute the chain. Each hook receives the accumulated payload.
     * If a hook returns { stop: true }, the chain halts.
     */
    async execute(initialPayload) {
        let payload = { ...initialPayload };
        const results = [];
        for (const hook of this.hooks) {
            // Check condition
            if (hook.condition && !hook.condition(payload)) {
                continue;
            }
            try {
                const result = await hook.fn(payload);
                results.push({ name: hook.name, result });
                // Merge result into payload for next hook
                if (result && typeof result === "object") {
                    payload = { ...payload, ...result };
                }
                // Stop chain if requested
                if (result?.stop)
                    break;
            }
            catch (err) {
                results.push({
                    name: hook.name,
                    error: err instanceof Error ? err.message : String(err),
                });
            }
        }
        return { payload, results };
    }
    /** Get hook names */
    getNames() {
        return this.hooks.map((h) => h.name);
    }
}
/**
 * Built-in hooks registry.
 *
 * Returns hook configurations that can be merged into settings.json.
 */
export function getBuiltinHooks() {
    return {
        "auto-lint": {
            event: "PostToolUse",
            description: "Run linter on written files",
            matcher: "file_write",
        },
        "auto-test": {
            event: "PostToolUse",
            description: "Run tests when test files are modified",
            matcher: "file_write",
        },
        "commit-guard": {
            event: "PreToolUse",
            description: "Block dangerous git/shell commands",
            matcher: "shell_exec",
        },
        "token-alert": {
            event: "Notification",
            description: "Warn when token usage exceeds threshold",
        },
    };
}
//# sourceMappingURL=builtin-hooks.js.map
