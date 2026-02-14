# Multi-Provider Guide

Use Ollama, Claude, Gemini, Codex, and Hugging Face with a single CLI.

---

## Supported Providers

| Provider | Provider Flag | API Key | Model Examples |
|----------|---------------|---------|----------------|
| **Ollama** | `--provider ollama` | None | `llama3.2`, `codellama`, `mistral` |
| **Claude** | `--provider claude` | `ANTHROPIC_API_KEY` | `claude-sonnet-4`, `claude-opus-4` |
| **Gemini** | `--provider gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash`, `gemini-1.5-pro` |
| **Codex** | `--provider codex` | `OPENAI_API_KEY` | `gpt-4.1`, `gpt-3.5-turbo` |
| **Hugging Face** | `--provider hf` | `HF_TOKEN` | `zai-org/GLM-4.7-Flash:novita`, `mistralai/Mistral-7B-Instruct-v0.3` |

---

## Setup

### 1. Set Your API Key(s)

```bash
# Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# Gemini
export GEMINI_API_KEY="AI..."

# OpenAI/Codex
export OPENAI_API_KEY="sk-..."

# Hugging Face
export HF_TOKEN="your-huggingface-token"
```

### 2. Set Default Provider

```bash
export OLLAMA_CLI_PROVIDER=claude
```

### 3. Verify Provider Health

```bash
cli-ollama serve
```

---

## Usage

### Using a Different Provider for One Command

```bash
# Use Claude
cli-ollama --provider claude run "Explain this"

# Use Gemini
cli-ollama --provider gemini run "Summarize this"

# Use Codex
cli-ollama --provider codex run "Refactor this"

# Use Hugging Face
cli-ollama --provider hf run "Answer this question"
```

### Switching Models

```bash
# Use a specific model with a provider
cli-ollama --provider claude --model claude-sonnet-4 run "Hello"
```

---

## Provider Comparison

| Feature | Ollama | Claude | Gemini | Codex | Hugging Face |
|---------|--------|--------|--------|-------|-------------|
| Local | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| Cost | Free* | $/token | $/token | $/token | $/token |
| Speed | Fast | Fast | Fast | Fast | Fast |
| Code | Good | Excellent | Good | Excellent | Good |
| Chat | Excellent | Excellent | Excellent | Excellent | Good |

*Local models are free, but require hardware

---

## Provider Routing

The CLI automatically routes requests based on the provider setting:

```
User Request
    ↓
Provider Router
    ↓
┌─────────────────┐
│ Ollama?         │ → Local server
│ Claude?         │ → Anthropic API
│ Gemini?         │ → Google API
│ Codex?          │ → OpenAI API
│ Hugging Face?   │ → Hugging Face API
└─────────────────┘
    ↓
Response
```

---

## Fallback Configuration

Set up automatic fallback if a provider is unavailable:

```python
# Example fallback chain
FALLBACK_CHAIN = ["ollama", "claude", "gemini", "codex", "hf"]
```

### How Fallback Works

When a request is made, the router tries the primary provider first. If that
provider fails (e.g. model not found, connection error, or authentication
failure), it automatically tries the next provider in the fallback chain.

**Important:** The router uses your **session's selected model** for the primary
provider. Fallback providers use their own default models so that a model name
that only exists on one provider is not sent to another.

For example, if you select `glm-5:cloud` with the Ollama provider and it fails,
the fallback to Claude will use `claude-sonnet-4-20250514` (Claude's default),
not `glm-5:cloud`.

### Model Auto-Discovery

At startup, the CLI queries the local Ollama server for available models. If the
configured model (`OLLAMA_MODEL`) is not found locally, the CLI:

1. Checks for a partial match (e.g. `llama3.2` matches `llama3.2:latest`)
2. If no match, auto-selects the first available model
3. Warns you about the selection

---

## API Key Management

### Best Practice: Use .env File

```bash
# Create .env file in your project
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
OPENAI_API_KEY=sk-...
HF_TOKEN=your-huggingface-token
OLLAMA_CLI_PROVIDER=ollama
```

### Best Practice: Don't Commit API Keys

Your `.env` file is in `.gitignore`:

```bash
# .gitignore
.env
```

---

## Provider-Specific Features

### Ollama

- Automatic installation via `install.sh`
- Local processing
- No API key required
- Supports custom models

### Claude

- Excellent coding abilities
- Long context support (200K tokens)
- Natural conversation flow

### Gemini

- Google's latest model
- Strong multimodal capabilities
- Fast inference

### Codex

- OpenAI's GPT models
- Mature ecosystem
- Best for general tasks

### Hugging Face

- Access to thousands of open-weight models
- Community-driven model development
- Cost-effective for experimentation
- Flexible model selection via router

---

## Cost Estimation

### Claude Pricing (approximate)

| Model | Input | Output |
|-------|-------|--------|
| Sonnet | $3/M tokens | $15/M tokens |
| Opus | $15/M tokens | $75/M tokens |

### Gemini Pricing (approximate)

| Model | Input | Output |
|-------|-------|--------|
| Flash | $0.35/M tokens | $1.05/M tokens |
| Pro | $7/M tokens | $21/M tokens |

### Codex Pricing (approximate)

| Model | Input | Output |
|-------|-------|--------|
| GPT-4 | $30/M tokens | $60/M tokens |
| GPT-3.5 | $0.50/M tokens | $1.50/M tokens |

*Ollama local models are free (excluding hardware costs)*

### Hugging Face Pricing (approximate)

Hugging Face pricing varies by model and usage tier. Most models through the router are priced competitively with other providers.

*Hugging Face models require an API token (HF_TOKEN)*

---

## Troubleshooting

### "Provider unavailable" error?

```bash
# Check your API key is set
echo $ANTHROPIC_API_KEY

# Check network connectivity
curl -X GET https://api.anthropic.com/v1/models
```

### "Invalid API key" error?

```bash
# Verify API key format
# Claude: sk-ant-...
# Gemini: AI...
# OpenAI: sk-...
# Hugging Face: hf_...
```

### "Model not found" error?

```bash
# Check available models for the provider
cli-ollama --provider ollama list
```
