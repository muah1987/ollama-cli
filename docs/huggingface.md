# Hugging Face Provider Guide

Access thousands of open-weight models through Hugging Face's router service.

---

## Introduction

The Hugging Face provider allows you to use models from the Hugging Face Hub through their router API. This gives you access to a wide variety of community-developed models with competitive pricing.

## Setup

### 1. Get Your API Token

1. Visit [Hugging Face](https://huggingface.co)
2. Sign in or create an account
3. Go to your profile → Settings → Access Tokens
4. Create a new token with read access
5. Copy the token

### 2. Set Your API Key

```bash
# In your terminal
export HF_TOKEN="your-huggingface-token"

# Or in your .env file
HF_TOKEN=your-huggingface-token
```

### 3. Verify Setup

```bash
# Check that the token is set
echo $HF_TOKEN

# Test the provider
qarin-cli --provider hf run "Say hello"
```

## Usage

### Basic Commands

```bash
# Use Hugging Face for a single request
qarin-cli --provider hf run "Explain quantum computing"

# Specify a particular model
qarin-cli --provider hf --model mistralai/Mistral-7B-Instruct-v0.3 run "Summarize this article"
```

### Available Models

Hugging Face provides access to thousands of models. Some popular options include:

- `zai-org/GLM-4.7-Flash:novita` (default)
- `mistralai/Mistral-7B-Instruct-v0.3`
- `meta-llama/Meta-Llama-3-8B-Instruct`
- `google/gemma-2-9b-it`
- `deepseek-ai/DeepSeek-Coder-V2-Instruct`

### Model Selection

When choosing a model, consider:
- **Task type**: Code models for programming, general models for other tasks
- **Size**: Larger models generally perform better but are slower
- **Cost**: Check pricing for your selected model
- **Context length**: Ensure the model supports your input size

## Features

### Model Variety

Access to a vast ecosystem of:
- Language models
- Code models
- Multimodal models
- Specialized domain models

### Community Innovation

- Rapidly evolving model landscape
- Cutting-edge research models
- Community fine-tuned variants

### Cost Effectiveness

Many models are priced competitively, making experimentation affordable.

## Model Information

### Default Model

The default model is `zai-org/GLM-4.7-Flash:novita`, chosen for its balance of quality and performance.

### Finding Models

Browse models at [Hugging Face Models](https://huggingface.co/models) or use:

```bash
# List available models (when supported by API)
qarin-cli --provider hf list
```

## Pricing

Hugging Face pricing varies by:
- Model selection
- Usage tier
- Billing plan

Visit [Hugging Face Pricing](https://huggingface.co/pricing) for detailed information.

*Most models are priced competitively with other cloud providers.*

## Configuration

### Environment Variables

```bash
# Required
HF_TOKEN=your-huggingface-token

# Optional (to set default provider)
QARIN_CLI_PROVIDER=hf
```

### Task-Specific Providers

You can set specific providers for different task types:

```bash
# Coding tasks use Hugging Face
QARIN_CLI_CODING_PROVIDER=hf
QARIN_CLI_CODING_MODEL=mistralai/Mistral-7B-Instruct-v0.3

# Agent tasks use Claude
QARIN_CLI_AGENT_PROVIDER=claude
QARIN_CLI_AGENT_MODEL=claude-sonnet-4
```

## Troubleshooting

### "Provider unavailable" error?

```bash
# Check your API key is set
echo $HF_TOKEN

# Verify the token format (should start with hf_...)
# Check network connectivity
curl -X GET https://huggingface.co/api/models -H "Authorization: Bearer $HF_TOKEN"
```

### "Invalid API key" error?

```bash
# Verify API key format
# Hugging Face tokens start with hf_...

# Test token validity
curl -X GET https://huggingface.co/api/whoami-v2 -H "Authorization: Bearer $HF_TOKEN"
```

### "Model not found" error?

```bash
# Verify the model name exists on Hugging Face
# Check if the model supports the task you're attempting
```

### Slow responses?

```bash
# Try a smaller/faster model
# Check your internet connection
# Consider using a model closer to your region
```

## Best Practices

1. **Start with the default**: The default model (`zai-org/GLM-4.7-Flash:novita`) is well-suited for most tasks
2. **Experiment wisely**: Use cheaper models for initial testing
3. **Monitor spending**: Keep track of usage to avoid unexpected costs
4. **Cache responses**: For repeated queries, consider local caching
5. **Combine providers**: Use Hugging Face for experimentation, cloud providers for production

## Limitations

- Requires internet connectivity
- May have rate limits depending on your account tier
- Response times vary based on model size and server load
- Not all models support all features (e.g., some may lack function calling)