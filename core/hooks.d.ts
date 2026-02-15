/**
 * Hook runner module.
 *
 * Ports the Python server/hook_runner.py into TypeScript.
 * Loads hook configuration from settings.json and dispatches
 * events to hook commands via subprocess.
 */
import type { HookResult } from "../types/agent.js";
/**
 * Hook runner that loads settings.json and executes hook commands.
 *
 * Supports 13 lifecycle events matching the Python implementation:
 * - SessionStart, SessionEnd
 * - PreToolUse, PostToolUse, PostToolUseFailure
 * - PreCompact
 * - UserPromptSubmit
 * - SkillTrigger
 * - SubagentStart, SubagentStop
 * - Notification
 * - PermissionRequest
 * - Stop
 */
export declare class HookRunner {
    private hooks;
    private readonly settingsPath;
    constructor(settingsPath?: string);
    /** Load hook configuration from settings.json */
    load(): Promise<void>;
    /** Check if hooks are enabled (settings file has hooks) */
    isEnabled(): boolean;
    /**
     * Execute all hooks registered for an event name.
     *
     * @param eventName - The event name (e.g. "PreToolUse", "SessionStart")
     * @param payload - JSON-serializable data sent to the hook on stdin
     * @param timeout - Maximum seconds to wait for each hook command
     * @returns List of HookResult, one per matching hook command
     */
    runHook(eventName: string, payload: Record<string, unknown>, timeout?: number): Promise<HookResult[]>;
    /** Check if a matcher pattern matches the payload */
    private matches;
    /** Run a single hook command via subprocess */
    private executeCommand;
}
//# sourceMappingURL=hooks.d.ts.map