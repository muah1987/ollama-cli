# Ollama CLI

**Get up and running with LLMs.**

Ollama CLI is a Python-based AI coding assistant powered by Ollama with multi-provider support. Seamlessly switch between local models and cloud providers like Claude, Gemini, and Codex.

---

## Installation

### One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash
```

This script will:
- Install uv if not present
- Clone or update ollama-cli
- Install Python dependencies
- Detect and install Ollama if missing

### Install from source

```bash
git clone https://github.com/muah1987/ollama-cli.git
cd ollama-cli
uv sync
```

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running

---

## Quick Start

```bash
# List available models
ollama-cli list

# Start an interactive chat
ollama-cli interactive

# Run a one-shot prompt
ollama-cli run "explain recursion in Python"

# Check server status
ollama-cli serve

# Show model details
ollama-cli show llama3.2

# List running models
ollama-cli ps

# Stop a running model
ollama-cli stop llama3.2

# Update configuration
ollama-cli config

# Show current session status
ollama-cli status

# Show version
ollama-cli version
```

---

## High-Performance Computing

### RDMA Acceleration

For high-performance networking with RDMA support:

```bash
# Detect RDMA devices
ollama-cli rdma detect

# Connect to RDMA device
ollama-cli rdma connect mlx5_0

# Check RDMA status
ollama-cli rdma status
```

### Apple Silicon Acceleration (MLX)

On macOS with Apple Silicon:

```bash
# Check MLX availability
ollama-cli accelerate check

# Enable MLX acceleration
ollama-cli accelerate enable

# Disable acceleration
ollama-cli accelerate disable
```

### Distributed Execution (EXO)

For distributed computing across nodes:

```bash
# Discover EXO cluster nodes
ollama-cli exo discover

# Check EXO status
ollama-cli exo status
```

---

## Multi-Provider Setup

### Claude (Anthropic)

```bash
ollama-cli --provider claude run "explain this error"
```

### Gemini (Google)

```bash
ollama-cli --provider gemini run "summarize this file"
```

### Codex (OpenAI)

```bash
ollama-cli --provider codex run "refactor this function"
```

---

## RDMA Support

### Supported Transports

Ollama CLI supports multiple RDMA transport protocols:

| Transport | Description | Use Case |
|-----------|-------------|----------|
| InfiniBand | Native RDMA protocol | High-performance clusters |
| RoCE v1 | RDMA over Converged Ethernet v1 | Data center networks |
| RoCE v2 | RDMA over Converged Ethernet v2 | Labeled subnet networks |
| iWARP | Internet Wide Area RDMA Protocol | Wide area networks |
| USB<>RDMA | USB-based RDMA adapters | External RDMA connectivity |
| Thunderbolt<>RDMA | Thunderbolt-based RDMA | High-speed connectivity |
| Network<>RDMA | Standard network cards | General purpose networking |

### Automatic Device Detection

```bash
# Detect all RDMA devices
ollama-cli rdma detect
```

---

## Configuration

Ollama CLI can be configured via environment variables: