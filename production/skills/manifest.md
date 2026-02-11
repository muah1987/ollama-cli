# Skills Manifest

This document lists all available skills in the Ollama CLI project.

## Skill: token_counter

**Description**: Advanced token counting and analysis for various providers

**Parameters**:
- `text` (str): Text to count tokens for
- `provider` (str, optional): Provider to use for token counting (default: "ollama")

**Returns**:
- `text` (str): The original text
- `token_count` (int): Estimated number of tokens
- `provider` (str): Provider used for counting
- `cost_estimate` (float): Estimated cost based on provider pricing
- `metrics` (dict): Detailed token metrics

## Skill: auto_compact

**Description**: Context auto-compaction management

**Parameters**:
- `action` (str): Action to perform ('check', 'compact', 'configure')
- `threshold` (float, optional): New compaction threshold (0.0-1.0)
- `keep_last_n` (int, optional): Number of recent messages to preserve

**Returns**:
- `action` (str): The action that was performed
- Additional fields depending on the action:
  - For 'check': context_usage, should_compact, total_tokens
  - For 'compact': compacted, compact_result, new_usage
  - For 'configure': configured, threshold, keep_last_n

## Usage Examples

```python
# Token counting
result = await execute_skill("token_counter", text="Hello, world!", provider="claude")
print(f"Tokens: {result['token_count']}, Cost: ${result['cost_estimate']:.4f}")

# Auto-compaction check
result = await execute_skill("auto_compact", action="check")
if result["should_compact"]:
    print("Context should be compacted")

# Configure auto-compaction
await execute_skill("auto_compact", action="configure", threshold=0.9, keep_last_n=2)
```