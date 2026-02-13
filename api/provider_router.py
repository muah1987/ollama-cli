#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""Multi-provider model router -- GOTCHA Tools layer, ATLAS Link phase.

Routes requests to Ollama, Claude, Gemini, or Codex based on task type.

Each provider wraps its respective API with a unified interface so the rest
of the system never needs to know which backend is handling a request.
The ProviderRouter reads environment-variable configuration to decide which
provider + model to use for each task type (coding, agent, subagent,
embedding) and implements automatic fallback when a provider is unavailable.
"""

from __future__ import annotations

import abc
import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

import httpx
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env early so all os.environ.get calls pick up the values
# ---------------------------------------------------------------------------

_env_candidates = [
    Path(__file__).resolve().parent.parent.parent / ".env",
    Path.cwd() / ".env",
]
for _candidate in _env_candidates:
    if _candidate.exists():
        load_dotenv(_candidate)
        break

# ---------------------------------------------------------------------------
# Lazy import: OllamaClient lives in the same package
# ---------------------------------------------------------------------------

from .ollama_client import OllamaClient, OllamaError, OllamaModelNotFoundError  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ProviderError(Exception):
    """Base exception for provider-related errors."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot be reached or is not responding."""


class ProviderAuthError(ProviderError):
    """Raised when authentication with a provider fails (missing or invalid key)."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT = 120.0

# Fallback priority: try these providers in order if the primary is down
_FALLBACK_CHAIN: list[str] = ["ollama", "claude", "gemini", "codex", "hf"]

# Default models per provider (used when no model is specified)
_DEFAULT_MODELS: dict[str, str] = {
    "ollama": "llama3.2",
    "claude": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.0-flash",
    "codex": "gpt-4.1",
    "hf": "zai-org/GLM-4.7-Flash:novita",
}

# Agent-specific model assignments (agent_type: (provider, model))
_AGENT_MODEL_MAP: dict[str, tuple[str, str]] = {}


def _load_agent_model_config() -> dict[str, tuple[str, str]]:
    """Load agent model assignments from environment and config."""
    config = {}

    # Load from environment variables
    agent_types = [
        "code", "research", "writer", "analysis", "planning",
        "review", "test", "debug", "docs", "orchestrator",
    ]
    for agent_type in agent_types:
        provider_var = f"OLLAMA_CLI_AGENT_{agent_type.upper()}_PROVIDER"
        model_var = f"OLLAMA_CLI_AGENT_{agent_type.upper()}_MODEL"

        provider = os.environ.get(provider_var)
        model = os.environ.get(model_var)

        if provider and model:
            config[agent_type] = (provider, model)

    # Load from config file
    config_file = Path(".ollama/settings.json")
    if config_file.exists():
        try:
            with open(config_file) as f:
                settings = json.load(f)
                agent_models = settings.get("agent_models", {})
                for agent_type, config_data in agent_models.items():
                    config[agent_type] = (
                        config_data.get("provider", "ollama"),
                        config_data.get("model", _DEFAULT_MODELS.get("ollama", "llama3.2")),
                    )
        except Exception:
            pass  # Ignore config errors

    return config


def initialize_agent_models() -> None:
    """Initialize agent model assignments at startup."""
    global _AGENT_MODEL_MAP
    _AGENT_MODEL_MAP = _load_agent_model_config()


def refresh_agent_models() -> None:
    """Refresh agent model assignments from configuration."""
    global _AGENT_MODEL_MAP
    _AGENT_MODEL_MAP.update(_load_agent_model_config())


# Initialize agent models at module load
initialize_agent_models()


# ---------------------------------------------------------------------------
# Abstract base provider
# ---------------------------------------------------------------------------


class BaseProvider(abc.ABC):
    """Abstract interface that every provider must implement.

    Attributes
    ----------
    name : str
        Human-readable provider identifier (e.g. ``"ollama"``, ``"claude"``).
    """

    name: str = ""

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Send a multi-turn chat completion request.

        Parameters
        ----------
        messages:
            Conversation history as ``[{"role": "user", "content": "..."}]``.
        model:
            Model identifier.  Falls back to the provider default if ``None``.
        stream:
            If ``True``, return an async iterator yielding partial results.
        **kwargs:
            Additional provider-specific parameters.
        """

    @abc.abstractmethod
    async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """Generate a single-turn completion from a plain prompt.

        Returns the generated text as a string.
        """

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Return ``True`` if the provider is reachable and authenticated."""

    @abc.abstractmethod
    async def list_models(self) -> list[str]:
        """Return a list of available model identifiers."""

    def get_token_count(self, text: str) -> int:
        """Estimate the number of tokens in *text*.

        Default heuristic: ~4 characters per token (English).  Subclasses may
        override with a provider-specific tokenizer.
        """
        return max(1, len(text) // 4)

    async def close(self) -> None:
        """Release any resources held by this provider.

        Subclasses should override to close HTTP clients, etc.
        """


# ---------------------------------------------------------------------------
# OllamaProvider -- delegates to the existing OllamaClient
# ---------------------------------------------------------------------------


class OllamaProvider(BaseProvider):
    """Provider backed by a local (or remote) Ollama instance.

    Wraps :class:`src.api_client.OllamaClient` so that it conforms to the
    :class:`BaseProvider` interface.  Supports cloud Ollama via
    ``OLLAMA_API_KEY`` for authenticated requests.
    """

    name = "ollama"

    def __init__(self, host: str | None = None, api_key: str | None = None) -> None:
        self._host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self._api_key = api_key or os.environ.get("OLLAMA_API_KEY", "")
        self._client = OllamaClient(host=self._host, api_key=self._api_key or None)
        self._default_model = os.environ.get("OLLAMA_MODEL", _DEFAULT_MODELS["ollama"])

    # -- BaseProvider implementation ----------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        return await self._client.chat(
            model=model or self._default_model,
            messages=messages,
            stream=stream,
            **kwargs,
        )

    async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        raw = await self._client.generate(
            model=model or self._default_model,
            prompt=prompt,
            stream=False,
            **kwargs,
        )
        result = cast(dict[str, Any], raw)
        return str(result.get("response", ""))

    async def health_check(self) -> bool:
        return await self._client.health_check()

    async def list_models(self) -> list[str]:
        models = await self._client.list_models()
        return [m["name"] for m in models]

    # -- Ollama-specific helpers -------------------------------------------

    async def embed(self, model: str, input_text: str) -> dict[str, Any]:
        """Proxy to the underlying embed endpoint (used for local embeddings)."""
        return await self._client.embed(model, input_text)

    async def close(self) -> None:
        await self._client.close()


# ---------------------------------------------------------------------------
# ClaudeProvider -- direct Anthropic API via httpx
# ---------------------------------------------------------------------------


class ClaudeProvider(BaseProvider):
    """Provider backed by the Anthropic Messages API.

    Requires ``ANTHROPIC_API_KEY`` in the environment.
    """

    name = "claude"

    _BASE_URL = "https://api.anthropic.com"
    _API_VERSION = "2023-06-01"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self._api_key:
            raise ProviderAuthError("ANTHROPIC_API_KEY is not set")
        self._default_model = _DEFAULT_MODELS["claude"]
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            timeout=httpx.Timeout(_DEFAULT_TIMEOUT),
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": self._API_VERSION,
                "content-type": "application/json",
            },
        )

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _convert_messages(messages: list[dict[str, str]]) -> tuple[str | None, list[dict[str, str]]]:
        """Split out a system message (Anthropic uses a top-level ``system`` field).

        Returns ``(system_text, user_messages)``.
        """
        system_text: str | None = None
        user_messages: list[dict[str, str]] = []
        for msg in messages:
            if msg.get("role") == "system":
                system_text = msg.get("content", "")
            else:
                user_messages.append(msg)
        return system_text, user_messages

    async def _stream_response(self, response: httpx.Response) -> AsyncIterator[dict[str, Any]]:
        """Parse Anthropic SSE stream into dicts."""
        try:
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or line.startswith("event:"):
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
        finally:
            await response.aclose()

    # -- BaseProvider implementation ----------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        system_text, user_messages = self._convert_messages(messages)

        payload: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": user_messages,
            "max_tokens": kwargs.pop("max_tokens", 4096),
            "stream": stream,
        }
        if system_text:
            payload["system"] = system_text
        payload.update(kwargs)

        if stream:
            req = self._client.build_request("POST", "/v1/messages", json=payload)
            response = await self._client.send(req, stream=True)
            if response.status_code == 401:
                await response.aclose()
                raise ProviderAuthError("Anthropic API key is invalid")
            if response.status_code >= 400:
                body = await response.aread()
                await response.aclose()
                raise ProviderError(f"Anthropic API error {response.status_code}: {body.decode()}")
            return self._stream_response(response)

        response = await self._client.post("/v1/messages", json=payload)
        if response.status_code == 401:
            raise ProviderAuthError("Anthropic API key is invalid")
        if response.status_code >= 400:
            raise ProviderError(f"Anthropic API error {response.status_code}: {response.text}")
        return response.json()

    async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": prompt}]
        raw = await self.chat(messages, model=model, stream=False, **kwargs)
        # Anthropic returns content as a list of blocks
        result = cast(dict[str, Any], raw)
        content = result.get("content", [])
        if isinstance(content, list) and content:
            return str(content[0].get("text", ""))
        return ""

    async def health_check(self) -> bool:
        try:
            # A minimal request to verify credentials
            response = await self._client.post(
                "/v1/messages",
                json={
                    "model": self._default_model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
            )
            return response.status_code in (200, 201)
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        # Anthropic does not expose a model listing endpoint; return known models
        return [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-haiku-3-5-20241022",
        ]

    async def close(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()


# ---------------------------------------------------------------------------
# GeminiProvider -- direct Google Generative AI REST API via httpx
# ---------------------------------------------------------------------------


class GeminiProvider(BaseProvider):
    """Provider backed by the Google Generative AI (Gemini) REST API.

    Requires ``GEMINI_API_KEY`` in the environment.
    """

    name = "gemini"

    _BASE_URL = "https://generativelanguage.googleapis.com"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            raise ProviderAuthError("GEMINI_API_KEY is not set")
        self._default_model = _DEFAULT_MODELS["gemini"]
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            timeout=httpx.Timeout(_DEFAULT_TIMEOUT),
            headers={"content-type": "application/json"},
        )

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _convert_messages(messages: list[dict[str, str]]) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert OpenAI-style messages to Gemini ``contents`` format.

        Returns ``(system_instruction, contents)``.
        """
        system_text: str | None = None
        contents: list[dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if role == "system":
                system_text = text
                continue
            # Gemini uses "user" and "model" roles
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": text}]})
        return system_text, contents

    # -- BaseProvider implementation ----------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        model_name = model or self._default_model
        system_text, contents = self._convert_messages(messages)

        payload: dict[str, Any] = {"contents": contents}
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        if "temperature" in kwargs:
            payload.setdefault("generationConfig", {})["temperature"] = kwargs.pop("temperature")
        if "max_tokens" in kwargs:
            payload.setdefault("generationConfig", {})["maxOutputTokens"] = kwargs.pop("max_tokens")

        endpoint = f"/v1beta/models/{model_name}:generateContent"
        params = {"key": self._api_key}

        if stream:
            endpoint = f"/v1beta/models/{model_name}:streamGenerateContent"
            params["alt"] = "sse"
            req = self._client.build_request("POST", endpoint, json=payload, params=params)
            response = await self._client.send(req, stream=True)
            if response.status_code == 401 or response.status_code == 403:
                await response.aclose()
                raise ProviderAuthError("Gemini API key is invalid")
            if response.status_code >= 400:
                body = await response.aread()
                await response.aclose()
                raise ProviderError(f"Gemini API error {response.status_code}: {body.decode()}")
            return self._stream_gemini(response)

        response = await self._client.post(endpoint, json=payload, params=params)
        if response.status_code in (401, 403):
            raise ProviderAuthError("Gemini API key is invalid")
        if response.status_code >= 400:
            raise ProviderError(f"Gemini API error {response.status_code}: {response.text}")
        return response.json()

    async def _stream_gemini(self, response: httpx.Response) -> AsyncIterator[dict[str, Any]]:
        """Parse Gemini SSE stream."""
        try:
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                try:
                    yield json.loads(data_str)
                except json.JSONDecodeError:
                    continue
        finally:
            await response.aclose()

    async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": prompt}]
        raw = await self.chat(messages, model=model, stream=False, **kwargs)
        # Extract text from Gemini response
        result = cast(dict[str, Any], raw)
        candidates = result.get("candidates", [])
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            if isinstance(first, dict):
                parts = first.get("content", {})
                if isinstance(parts, dict):
                    part_list = parts.get("parts", [])
                    if isinstance(part_list, list) and part_list:
                        first_part = part_list[0]
                        if isinstance(first_part, dict):
                            return str(first_part.get("text", ""))
        return ""

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                f"/v1beta/models/{self._default_model}",
                params={"key": self._api_key},
            )
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        try:
            response = await self._client.get(
                "/v1beta/models",
                params={"key": self._api_key},
            )
            if response.status_code != 200:
                return []
            data = response.json()
            models_list = data.get("models", [])
            if not isinstance(models_list, list):
                return []
            result: list[str] = []
            for m in models_list:
                if isinstance(m, dict):
                    name = m.get("name", "")
                    if isinstance(name, str):
                        result.append(name.removeprefix("models/"))
            return result
        except (httpx.ConnectError, httpx.TimeoutException):
            return []

    async def close(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()


# ---------------------------------------------------------------------------
# CodexProvider -- OpenAI-compatible API via httpx
# ---------------------------------------------------------------------------


class CodexProvider(BaseProvider):
    """Provider backed by the OpenAI Chat Completions API (GPT-4, etc.).

    Named "codex" to distinguish from the Ollama OpenAI-compatible shim.
    Requires ``OPENAI_API_KEY`` in the environment.
    """

    name = "codex"

    _BASE_URL = "https://api.openai.com"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self._api_key:
            raise ProviderAuthError("OPENAI_API_KEY is not set")
        self._default_model = _DEFAULT_MODELS["codex"]
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            timeout=httpx.Timeout(_DEFAULT_TIMEOUT),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

    # -- internal helpers ---------------------------------------------------

    async def _stream_openai(self, response: httpx.Response) -> AsyncIterator[dict[str, Any]]:
        """Parse OpenAI SSE stream into dicts."""
        try:
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    yield json.loads(data_str)
                except json.JSONDecodeError:
                    continue
        finally:
            await response.aclose()

    # -- BaseProvider implementation ----------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        payload: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": messages,
            "stream": stream,
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs.pop("max_tokens")
        if "temperature" in kwargs:
            payload["temperature"] = kwargs.pop("temperature")
        payload.update(kwargs)

        if stream:
            req = self._client.build_request("POST", "/v1/chat/completions", json=payload)
            response = await self._client.send(req, stream=True)
            if response.status_code == 401:
                await response.aclose()
                raise ProviderAuthError("OpenAI API key is invalid")
            if response.status_code >= 400:
                body = await response.aread()
                await response.aclose()
                raise ProviderError(f"OpenAI API error {response.status_code}: {body.decode()}")
            return self._stream_openai(response)

        response = await self._client.post("/v1/chat/completions", json=payload)
        if response.status_code == 401:
            raise ProviderAuthError("OpenAI API key is invalid")
        if response.status_code >= 400:
            raise ProviderError(f"OpenAI API error {response.status_code}: {response.text}")
        return response.json()

    async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": prompt}]
        raw = await self.chat(messages, model=model, stream=False, **kwargs)
        result = cast(dict[str, Any], raw)
        choices = result.get("choices", [])
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message", {})
                if isinstance(message, dict):
                    return str(message.get("content", ""))
        return ""

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/v1/models")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        try:
            response = await self._client.get("/v1/models")
            if response.status_code != 200:
                return []
            data = response.json()
            data_list = data.get("data", [])
            if not isinstance(data_list, list):
                return []
            result: list[str] = []
            for m in data_list:
                if isinstance(m, dict):
                    model_id = m.get("id", "")
                    if isinstance(model_id, str):
                        result.append(model_id)
            return result
        except (httpx.ConnectError, httpx.TimeoutException):
            return []

    async def close(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()


# ---------------------------------------------------------------------------
# HfProvider -- OpenAI-compatible API via Hugging Face Router
# ---------------------------------------------------------------------------


class HfProvider(BaseProvider):
    """Provider backed by the Hugging Face Router API.

    Requires ``HF_TOKEN`` in the environment.
    Uses the OpenAI-compatible API format.
    """

    name = "hf"

    _BASE_URL = "https://router.huggingface.co/v1"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("HF_TOKEN", "")
        if not self._api_key:
            raise ProviderAuthError("HF_TOKEN is not set")
        self._default_model = _DEFAULT_MODELS.get("hf", "zai-org/GLM-4.7-Flash:novita")
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            timeout=httpx.Timeout(_DEFAULT_TIMEOUT),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

    # -- internal helpers ---------------------------------------------------

    async def _stream_openai(self, response: httpx.Response) -> AsyncIterator[dict[str, Any]]:
        """Parse OpenAI SSE stream into dicts."""
        try:
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    yield json.loads(data_str)
                except json.JSONDecodeError:
                    continue
        finally:
            await response.aclose()

    # -- BaseProvider implementation ----------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        payload: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": messages,
            "stream": stream,
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs.pop("max_tokens")
        if "temperature" in kwargs:
            payload["temperature"] = kwargs.pop("temperature")
        payload.update(kwargs)

        if stream:
            req = self._client.build_request("POST", "/chat/completions", json=payload)
            response = await self._client.send(req, stream=True)
            if response.status_code == 401:
                await response.aclose()
                raise ProviderAuthError("Hugging Face API key is invalid")
            if response.status_code >= 400:
                body = await response.aread()
                await response.aclose()
                raise ProviderError(f"Hugging Face API error {response.status_code}: {body.decode()}")
            return self._stream_openai(response)

        response = await self._client.post("/chat/completions", json=payload)
        if response.status_code == 401:
            raise ProviderAuthError("Hugging Face API key is invalid")
        if response.status_code >= 400:
            raise ProviderError(f"Hugging Face API error {response.status_code}: {response.text}")
        return response.json()

    async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": prompt}]
        raw = await self.chat(messages, model=model, stream=False, **kwargs)
        result = cast(dict[str, Any], raw)
        choices = result.get("choices", [])
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message", {})
                if isinstance(message, dict):
                    return str(message.get("content", ""))
        return ""

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        try:
            response = await self._client.get("/models")
            if response.status_code != 200:
                return []
            data = response.json()
            data_list = data.get("data", [])
            if not isinstance(data_list, list):
                return []
            result: list[str] = []
            for m in data_list:
                if isinstance(m, dict):
                    model_id = m.get("id", "")
                    if isinstance(model_id, str):
                        result.append(model_id)
            return result
        except (httpx.ConnectError, httpx.TimeoutException):
            return []

    async def close(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()


# ---------------------------------------------------------------------------
# Task routing configuration
# ---------------------------------------------------------------------------


_TASK_ENV_MAP: dict[str, tuple[str, str, str, str]] = {
    # task_type: (provider_env_var, model_env_var, default_provider, default_model)
    "coding": (
        "OLLAMA_CLI_CODING_PROVIDER",
        "OLLAMA_CLI_CODING_MODEL",
        "ollama",
        "codestral:latest",
    ),
    "agent": (
        "OLLAMA_CLI_AGENT_PROVIDER",
        "OLLAMA_CLI_AGENT_MODEL",
        "ollama",
        "llama3.2",
    ),
    "subagent": (
        "OLLAMA_CLI_SUBAGENT_PROVIDER",
        "OLLAMA_CLI_SUBAGENT_MODEL",
        "ollama",
        "glm-ocr",
    ),
    "embedding": (
        "",
        "",
        "ollama",
        "nomic-embed-text",
    ),
}


# ---------------------------------------------------------------------------
# ProviderRouter
# ---------------------------------------------------------------------------


class ProviderRouter:
    """Route requests to the appropriate provider based on task type.

    On construction the router reads environment variables to decide which
    provider and model to use for each task type.  It lazily instantiates
    provider instances and caches them for reuse.

    Fallback chain
    --------------
    If the primary provider for a task is unavailable, the router will try
    each provider in :data:`_FALLBACK_CHAIN` order until one succeeds.
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._task_config: dict[str, tuple[str, str]] = {}

        # Pre-compute per-task (provider_name, model) from env
        for task_type, (prov_env, model_env, default_prov, default_model) in _TASK_ENV_MAP.items():
            provider_name = os.environ.get(prov_env, default_prov) if prov_env else default_prov
            model_name = os.environ.get(model_env, default_model) if model_env else default_model
            self._task_config[task_type] = (provider_name, model_name)

    def set_agent_model(self, agent_type: str, provider: str, model: str) -> None:
        """Set a specific provider and model for an agent type."""
        _AGENT_MODEL_MAP[agent_type] = (provider, model)

    def get_agent_model(self, agent_type: str) -> tuple[str, str] | None:
        """Get the provider and model for a specific agent type."""
        return _AGENT_MODEL_MAP.get(agent_type)

    # -- provider construction (lazy, cached) --------------------------------

    def _build_provider(self, name: str) -> BaseProvider:
        """Construct a provider instance by name.

        Raises :class:`ProviderAuthError` if required credentials are missing.
        """
        name = name.lower()
        if name == "ollama":
            return OllamaProvider()
        if name == "claude":
            return ClaudeProvider()
        if name == "gemini":
            return GeminiProvider()
        if name == "codex":
            return CodexProvider()
        if name == "hf":
            return HfProvider()
        raise ProviderError(f"Unknown provider: {name!r}")

    def get_provider(self, name: str) -> BaseProvider:
        """Return a cached provider instance by name.

        Raises :class:`ProviderError` if the name is unknown.
        Raises :class:`ProviderAuthError` if credentials are missing.
        """
        name = name.lower()
        if name not in self._providers:
            self._providers[name] = self._build_provider(name)
        return self._providers[name]

    # -- routing -------------------------------------------------------------

    async def route(
        self,
        task_type: str,
        messages: list[dict[str, str]],
        agent_type: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Route a chat request based on *task_type*.

        Parameters
        ----------
        task_type:
            One of ``"coding"``, ``"agent"``, ``"subagent"``, ``"embedding"``.
        messages:
            Conversation history.
        agent_type:
            Specific agent type for custom model assignment.
        model:
            Explicit model override.  When provided, this model is used
            instead of the default resolved from the task configuration.
        **kwargs:
            Forwarded to the provider's ``chat`` method.

        Returns
        -------
        The provider response (dict or async iterator if streaming).

        Raises
        ------
        ProviderUnavailableError
            If no provider in the fallback chain can serve the request.
        """
        # Check if we have a specific agent model assignment
        if provider:
            primary_provider = provider.lower()
            if task_type not in self._task_config:
                raise ProviderError(f"Unknown task type: {task_type!r}. Expected one of: {', '.join(self._task_config)}")
            _, resolved_model = self._task_config[task_type]
        elif agent_type and agent_type in _AGENT_MODEL_MAP:
            primary_provider, resolved_model = _AGENT_MODEL_MAP[agent_type]
        elif task_type not in self._task_config:
            raise ProviderError(f"Unknown task type: {task_type!r}. Expected one of: {', '.join(self._task_config)}")
        else:
            primary_provider, resolved_model = self._task_config[task_type]

        # Caller-supplied model takes precedence over task/agent defaults
        if model:
            resolved_model = model

        # Build an ordered attempt list: primary first, then the rest of the chain
        attempt_order = [primary_provider] + [p for p in _FALLBACK_CHAIN if p != primary_provider]

        last_error: Exception | None = None
        for provider_name in attempt_order:
            try:
                provider = self.get_provider(provider_name)
            except ProviderAuthError:
                # No credentials -- skip to next
                continue

            # Use the resolved model for the primary provider; for fallback
            # providers, switch to their own default model so we don't send
            # a model name that only exists on another provider.
            effective_model = (
                resolved_model if provider_name == primary_provider
                else _DEFAULT_MODELS.get(provider_name, resolved_model)
            )

            try:
                return await provider.chat(messages, model=effective_model, **kwargs)
            except OllamaModelNotFoundError as exc:
                # Model not found on Ollama -- try to auto-select a locally
                # available model before falling through to other providers.
                if provider_name == "ollama":
                    try:
                        available = await provider.list_models()
                        if available:
                            fallback_model = available[0]
                            logger.warning(
                                "Model %r not found on Ollama; retrying with %r",
                                effective_model,
                                fallback_model,
                            )
                            try:
                                return await provider.chat(messages, model=fallback_model, **kwargs)
                            except (ProviderError, OllamaError) as inner:
                                last_error = inner
                                continue
                    except Exception:
                        pass  # list_models failed; fall through normally
                last_error = exc
                continue
            except (ProviderError, OllamaError, httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                continue

        raise ProviderUnavailableError(f"All providers exhausted for task_type={task_type!r}. Last error: {last_error}")

    # -- health / introspection ----------------------------------------------

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all providers that have valid credentials.

        Returns a dict mapping provider name to health status.
        """
        results: dict[str, bool] = {}
        for name in _FALLBACK_CHAIN:
            try:
                provider = self.get_provider(name)
                results[name] = await provider.health_check()
            except ProviderAuthError:
                results[name] = False
        return results

    def list_available_providers(self) -> list[str]:
        """List provider names for which valid API keys are configured.

        Ollama is always considered available (no key required).
        """
        available: list[str] = ["ollama"]  # Ollama needs no key

        key_map: dict[str, str] = {
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "codex": "OPENAI_API_KEY",
            "hf": "HF_TOKEN",
        }
        for provider_name, env_var in key_map.items():
            if os.environ.get(env_var, ""):
                available.append(provider_name)

        return available

    async def close(self) -> None:
        """Close all cached provider HTTP clients."""
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    async def _test() -> None:
        router = ProviderRouter()

        print("Available providers:", router.list_available_providers())
        print()

        print("Task routing configuration:")
        for task_type, (prov, model) in router._task_config.items():
            print(f"  {task_type:10s} -> provider={prov}, model={model}")
        print()

        print("Health checks:")
        health = await router.health_check_all()
        for name, status in health.items():
            icon = "OK" if status else "UNAVAILABLE"
            print(f"  {name:10s} -> {icon}")

        await router.close()

    asyncio.run(_test())
