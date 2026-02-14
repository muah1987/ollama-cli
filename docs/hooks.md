# Hooks System

Customize Ollama CLI behavior with 14 lifecycle hooks.

---

## Overview

Ollama CLI provides 14 lifecycle hooks that execute at specific points during execution.
Hooks follow the **skill→hook→.py pipeline**: a skill triggers a hook event, the hook
dispatches to one or more `.py` scripts, and the scripts can modify behavior.

| # | Hook | When It Fires | Use Cases |
|---|------|---------------|-----------|
| 1 | `Setup` | On init or periodic maintenance | Load git status, inject context, environment persistence |
| 2 | `SessionStart` | When a session begins | Initialize state, load context, load OLLAMA.md |
| 3 | `SessionEnd` | When a session ends | Save summaries, persist memory, cleanup |
| 4 | `UserPromptSubmit` | Before processing user input | Validate input, security filtering, prompt logging |
| 5 | `PreToolUse` | Before tool execution | Validate inputs, gate operations, block dangerous commands |
| 6 | `PostToolUse` | After tool completes | Log results, transform output, trigger follow-ups |
| 7 | `PostToolUseFailure` | When a tool execution fails | Structured error logging with full context |
| 8 | `PermissionRequest` | On permission dialog | Permission auditing, auto-allow read-only ops |
| 9 | `SkillTrigger` | When a skill invokes a hook | Skill→hook routing, pre-processing, logging |
| 10 | `PreCompact` | Before context compaction | Extract key information, save snapshots |
| 11 | `Stop` | When the model finishes responding | Final cleanup, completion notifications |
| 12 | `SubagentStart` | When a subagent spawns | Subagent spawn logging, announcements |
| 13 | `SubagentStop` | When a subagent finishes | Subagent completion logging |
| 14 | `Notification` | On notable events | Alerts, notifications, TTS |

---

## Hook Configuration

### Location

Configuration is in `.ollama/settings.json`:

```json
{
  "hooks": {
    "Setup": [],
    "SessionStart": [],
    "SessionEnd": [],
    "UserPromptSubmit": [],
    "PreToolUse": [],
    "PostToolUse": [],
    "PostToolUseFailure": [],
    "PermissionRequest": [],
    "SkillTrigger": [],
    "PreCompact": [],
    "Stop": [],
    "SubagentStart": [],
    "SubagentStop": [],
    "Notification": []
  }
}
```

### Hook Format

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "pattern",  // Optional: regex to match
        "hooks": [
          {
            "type": "command",
            "command": "python script.py"
          },
          {
            "type": "python",
            "module": "module.function"
          }
        ]
      }
    ]
  }
}
```

---

## Hook Payload

Each hook receives JSON on stdin:

```json
{
  "hook": "HookName",
  "timestamp": "2024-01-01T00:00:00Z",
  "session_id": "abc123",
  "model": "llama3.2",
  "provider": "ollama",
  "data": {
    "messages": [...],
    "context": {...}
  }
}
```

---

## Built-in Hooks

### Setup

Runs on init or periodic maintenance. Use cases:
- Load git status and recent issues
- Inject development context
- Environment persistence via `OLLAMA_ENV_FILE`
- Load context files (OLLAMA.md, .ollamaignore)

### SessionStart

Runs when a session begins. Use cases:
- Load project context from OLLAMA.md
- Initialize user preferences
- Load external knowledge bases

### SessionEnd

Runs when a session ends. Use cases:
- Save conversation summary
- Persist memory entries
- Send notification
- Cleanup temp files and stale logs

### UserPromptSubmit

Runs immediately when user submits a prompt (before model processes it). Use cases:
- Prompt validation and security filtering
- Prompt logging
- Context injection
- Block dangerous or sensitive prompts

### PreToolUse

Runs before tool execution. Use cases:
- Validate tool inputs
- Enforce access policies (block `rm -rf`, `.env` access)
- Modify tool inputs

### PostToolUse

Runs after tool completion. Use cases:
- Log tool results
- Transform output
- Trigger follow-up actions

### PostToolUseFailure

Runs when a tool execution fails. Use cases:
- Structured error logging with timestamps
- Error classification (permission, not_found, timeout, network)
- Full context capture for debugging

### PermissionRequest

Runs when user is shown a permission dialog. Use cases:
- Permission auditing
- Auto-allow read-only ops (Read, Glob, Grep, safe Bash like `ls`, `cat`, `pwd`)
- Auto-deny dangerous operations

### SkillTrigger

Runs when a skill invokes a hook (skill→hook→.py pipeline). Use cases:
- Route skill invocations to downstream hooks
- Pre-process skill parameters
- Log skill usage

### PreCompact

Runs before context compaction. Use cases:
- Extract key information
- Save important messages
- Annotate content
- Transcript backup

### Stop

Runs when the model finishes responding. Use cases:
- Final state cleanup
- AI-generated completion messages
- Save model state

### SubagentStart

Runs when a subagent (via `@agent` commands) spawns. Use cases:
- Subagent spawn logging
- Resource allocation tracking
- Optional announcements

### SubagentStop

Runs when a subagent finishes responding. Use cases:
- Subagent completion logging
- Result aggregation
- Resource cleanup

### Notification

Runs on notable events. Use cases:
- Send alerts
- Log events
- Trigger external actions

---

## Hook Types

### Command Hook

 Executes shell commands:

```json
{
  "type": "command",
  "command": "python .ollama/hooks/session_start.py",
  "shell": true
}
```

### Python Hook

 Executes Python functions:

```json
{
  "type": "python",
  "module": "my_module.hook_handler",
  "function": "on_session_start"
}
```

### Webhook Hook

 Sends HTTP requests:

```json
{
  "type": "webhook",
  "url": "http://localhost:8000/hook",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

---

## Environment Variables

Hooks have access to these environment variables:

| Variable | Description |
|----------|-------------|
| `OLLAMA_PROJECT_DIR` | Project directory |
| `OLLAMA_SESSION_ID` | Current session ID |
| `OLLAMA_MODEL` | Active model |
| `OLLAMA_PROVIDER` | Active provider |
| `OLLAMA_HOOKS_ENABLED` | Hook system status |

---

## Examples

### Logging Hook

```python
# .ollama/hooks/logger.py
import json
import logging
from pathlib import Path

def on_post_tool_use(payload: dict) -> dict:
    """Log tool usage to a file."""
    log_file = Path.home() / ".ollama" / "tool_logs.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a") as f:
        f.write(json.dumps(payload) + "\n")

    return {"logged": True}

if __name__ == "__main__":
    payload = json.loads(input())
    result = on_post_tool_use(payload)
    print(json.dumps(result))
```

### Policy Hook

```python
# .ollama/hooks/policy.py
import json

def on_pre_tool_use(payload: dict) -> dict:
    """Enforce policy - deny dangerous operations."""
    if payload.get("tool") == "bash":
        command = payload.get("command", "")
        if "rm -rf" in command or "dd if=" in command:
            return {
                "permissionDecision": "deny",
                "reason": "Dangerous command detected"
            }
    return {"permissionDecision": "allow"}

if __name__ == "__main__":
    payload = json.loads(input())
    result = on_pre_tool_use(payload)
    print(json.dumps(result))
```

### Notification Hook

```python
# .ollama/hooks/notify.py
import json
import requests

def on_session_end(payload: dict) -> dict:
    """Send notification on session end."""
    webhook_url = payload.get("webhook_url")
    if not webhook_url:
        return {"notified": False}

    summary = payload.get("summary", {})
    requests.post(webhook_url, json={
        "text": f"Session ended: {summary.get('total_tokens', 0)} tokens used"
    })

    return {"notified": True}

if __name__ == "__main__":
    payload = json.loads(input())
    result = on_session_end(payload)
    print(json.dumps(result))
```

---

## Debugging Hooks

### Enable Verbose Mode

```bash
cli-ollama --verbose interactive
```

### Test Hook Manually

```bash
echo '{"hook": "TestHook", "data": {"test": true}}' | \
  python .ollama/hooks/session_start.py
```

### Check Hook Configuration

```bash
cat .ollama/settings.json | python -m json.tool
```

---

## Hook Order

Hooks execute in order within each event:

1. `PreToolUse` hooks run first
2. Tool executes
3. `PostToolUse` hooks run
4. Continue...

---

## Best Practices

1. **Keep hooks fast** - Avoid blocking operations
2. **Handle errors gracefully** - Return error info, don't crash
3. **Use timeout** - Set reasonable timeouts for external calls
4. **Log issues** - Write hook errors to log files
5. **Test in isolation** - Test hooks before enabling
