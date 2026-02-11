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

## Skill: mlx_acceleration

**Description**: Apple Metal GPU acceleration via MLX framework for Apple Silicon

**Parameters**:
- `action` (str): Action to perform ('check', 'enable', 'disable')

**Returns**:
- `action` (str): The action that was performed
- `available` (bool): Whether MLX acceleration is available
- `device_info` (dict): Information about the GPU device

## Skill: exo_execution

**Description**: Distributed execution optimization via EXO framework

**Parameters**:
- `action` (str): Action to perform ('check', 'discover', 'execute')
- `task` (dict): Task description for execution

**Returns**:
- `action` (str): The action that was performed
- `initialized` (bool): Whether EXO was initialized
- `node_count` (int): Number of nodes in the cluster
- `nodes` (list): List of available nodes

## Skill: rdma_acceleration

**Description**: RDMA network acceleration for high-performance communication

**Parameters**:
- `action` (str): Action to perform ('check', 'connect', 'disconnect', 'status')
- `device` (str): RDMA device name for connection operations

**Returns**:
- `action` (str): The action that was performed
- `initialized` (bool): Whether RDMA was initialized
- `device_count` (int): Number of RDMA devices detected
- `devices` (list): List of detected RDMA devices

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

# Check MLX acceleration availability
result = await execute_skill("mlx_acceleration", action="check")
if result["available"]:
    print(f"MLX acceleration available: {result['device_info']}")

# Discover EXO cluster nodes
result = await execute_skill("exo_execution", action="discover")
print(f"Found {result['node_count']} nodes")

# Connect to RDMA device
result = await execute_skill("rdma_acceleration", action="connect", device="mlx5_0")
if result["connected"]:
    print(f"Connected to {result['device']}")
```