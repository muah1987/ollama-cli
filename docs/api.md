# API Reference

Ollama CLI provides a REST API compatible with Ollama's OpenAI-compatible API.

---

## Base URL

```
http://localhost:11434/api
```

Configure with `OLLAMA_HOST` environment variable.

---

## Endpoints

### Generate

Generate completions from a model.

**Endpoint:** `POST /api/generate`

**Request:**

```json
{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?",
  "stream": false
}
```

**Response:**

```json
{
  "model": "llama3.2",
  "response": "The sky appears blue because...",
  "context": [1, 2, 3, ...],
  "done": true
}
```

---

### Chat

Chat with a model.

**Endpoint:** `POST /api/chat`

**Request:**

```json
{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "stream": false
}
```

**Response:**

```json
{
  "model": "llama3.2",
  "message": {
    "role": "assistant",
    "content": "Hello! How can I help?"
  },
  "done": true
}
```

---

### List Models

List available models.

**Endpoint:** `GET /api/tags`

**Response:**

```json
{
  "models": [
    {
      "name": "llama3.2",
      "modified_at": "2024-01-01T00:00:00Z",
      "size": 1234567890
    }
  ]
}
```

---

### Show Model Information

Get details about a model.

**Endpoint:** `POST /api/show`

**Request:**

```json
{
  "model": "llama3.2"
}
```

---

### Create Model

Create a model from a Modelfile.

**Endpoint:** `POST /api/create`

**Request:**

```json
{
  "model": "mymodel",
  "modelfile": "FROM llama3.2\nSYSTEM You are a helpful assistant."
}
```

---

### Pull Model

Pull a model from the registry.

**Endpoint:** `POST /api/pull`

**Request:**

```json
{
  "model": "llama3.2",
  "stream": false
}
```

---

### Delete Model

Delete a local model.

**Endpoint:** `DELETE /api/delete`

**Request:**

```json
{
  "model": "mymodel"
}
```

---

### Copy Model

Copy a model.

**Endpoint:** `POST /api/copy`

**Request:**

```json
{
  "source": "llama3.2",
  "destination": "mycopy"
}
```

---

### Running Models

List running models.

**Endpoint:** `GET /api/ps`

**Response:**

```json
{
  "models": [
    {
      "name": "llama3.2",
      "pid": 12345,
      "memory": 1234567890
    }
  ]
}
```

---

## Authentication

The Ollama API does not require authentication by default. For cloud providers:

| Provider | Header |
|----------|--------|
| Claude | `x-api-key: sk-ant-...` |
| Gemini | `x-goog-api-key: AI...` |
| Codex | `Authorization: Bearer sk-...` |

---

## Streaming

Most endpoints support streaming responses. Set `"stream": true` to enable.

**Stream Response Format:**

Each chunk is a JSON object on its own line:

```json
{"model":"llama3.2","response":"The","done":false}
{"model":"llama3.2","response":" sky","done":false}
{"model":"llama3.2","response":" is","done":false}
{"model":"llama3.2","response":" blue","done":true}
```

---

## Error Responses

**400 Bad Request:**

```json
{
  "error": "invalid model name"
}
```

**500 Internal Server Error:**

```json
{
  "error": "failed to generate response"
}
```

---

## Python Client Example

```python
import httpx

async def chat_with_ollama():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "stream": False
            }
        )
        return response.json()

result = await chat_with_ollama()
print(result["message"]["content"])
```