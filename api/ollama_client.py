#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""
Ollama API client -- GOTCHA Tools layer, ATLAS Trace phase.

Async HTTP client wrapping the native Ollama REST API and the OpenAI-compatible
endpoint.  All methods are async, using httpx.AsyncClient internally.

Supports:
- Chat completions (native + OpenAI-compatible)
- Single-prompt generation
- Embeddings
- Model management (list, show, pull)
- Health checks and version queries
- Token metrics extraction
- Streaming (NDJSON) for chat, generate, and pull operations

Retry logic: 3 retries with exponential backoff (1s, 2s, 4s) for connection errors.
Default timeout: 300 seconds.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .errors import OllamaConnectionError, OllamaError, OllamaModelNotFoundError


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_TIMEOUT = 300.0
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # seconds; retries at 1s, 2s, 4s


# ---------------------------------------------------------------------------
# OllamaClient
# ---------------------------------------------------------------------------


class OllamaClient:
    """Async client for the Ollama REST API.

    Supports both local Ollama (``http://localhost:11434``) and cloud Ollama
    (``https://ollama.com``) with API key authentication.

    Parameters
    ----------
    host:
        Base URL of the Ollama server (e.g. ``http://localhost:11434``
        or ``https://ollama.com``).
    timeout:
        Default request timeout in seconds.
    api_key:
        Optional API key for authenticated requests (``Authorization:
        Bearer <key>``).  When *not provided* (``None``), the
        ``OLLAMA_API_KEY`` environment variable is checked.  An explicit
        empty string disables env-based auth.  Local servers typically
        need no key.
    """

    def __init__(
        self,
        host: str = _DEFAULT_HOST,
        timeout: float = _DEFAULT_TIMEOUT,
        api_key: str | None = None,
    ) -> None:
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._api_key: str = api_key if api_key is not None else os.environ.get("OLLAMA_API_KEY", "")
        self._client: httpx.AsyncClient | None = None

    # -- lifecycle -----------------------------------------------------------

    def _get_client(self) -> httpx.AsyncClient:
        """Return the shared async client, creating it lazily."""
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.host,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> OllamaClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # -- internal helpers ----------------------------------------------------

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> httpx.Response:
        """Issue an HTTP request with retry + exponential backoff on connection errors.

        Returns the raw ``httpx.Response``.  When *stream* is True the response
        is returned **un-read** (caller must iterate / close it).
        """
        client = self._get_client()
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                if stream:
                    req = client.build_request(method, path, json=json_body)
                    response = await client.send(req, stream=True)
                else:
                    response = await client.request(method, path, json=json_body)

                # Handle model-not-found (Ollama returns 404)
                if response.status_code == 404:
                    body = response.text if not stream else ""
                    raise OllamaModelNotFoundError(f"Model not found (HTTP 404): {body}")

                response.raise_for_status()
                return response

            except httpx.ConnectError as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_BASE * (2**attempt)
                    await asyncio.sleep(wait)
                    continue
                raise OllamaConnectionError(
                    f"Cannot connect to Ollama at {self.host} after {_MAX_RETRIES} attempts"
                ) from exc

            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_BASE * (2**attempt)
                    await asyncio.sleep(wait)
                    continue
                raise OllamaConnectionError(
                    f"Request to Ollama timed out after {self.timeout}s ({_MAX_RETRIES} attempts)"
                ) from exc

            except (OllamaModelNotFoundError, OllamaError):
                raise

            except httpx.HTTPStatusError as exc:
                raise OllamaError(f"HTTP {exc.response.status_code}: {exc.response.text}") from exc

        # Should not reach here, but just in case
        raise OllamaConnectionError(f"Request failed after {_MAX_RETRIES} retries") from last_exc

    async def _stream_response(self, response: httpx.Response) -> AsyncIterator[dict[str, Any]]:
        """Read NDJSON lines from a streaming httpx response, yielding parsed dicts.

        Each line from the Ollama streaming API is a JSON object terminated by a
        newline.  Blank lines and JSON decode errors are silently skipped.
        """
        try:
            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
        finally:
            await response.aclose()

    # -- core methods --------------------------------------------------------

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Send a chat completion request.

        POST ``/api/chat``

        Parameters
        ----------
        model:
            Model name (e.g. ``llama3.2``).
        messages:
            Conversation history as ``[{"role": "user", "content": "..."}]``.
        stream:
            If True, return an async iterator of JSON chunks.
        **kwargs:
            Additional Ollama parameters (``temperature``, ``top_p``, ``system``, etc.).
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }

        response = await self._request_with_retry("POST", "/api/chat", json_body=payload, stream=stream)

        if stream:
            return self._stream_response(response)
        return response.json()

    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Generate a completion from a single prompt.

        POST ``/api/generate``

        Parameters
        ----------
        model:
            Model name.
        prompt:
            The input prompt string.
        stream:
            If True, return an async iterator of JSON chunks.
        **kwargs:
            Additional Ollama parameters.
        """
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs,
        }

        response = await self._request_with_retry("POST", "/api/generate", json_body=payload, stream=stream)

        if stream:
            return self._stream_response(response)
        return response.json()

    async def embed(self, model: str, input_text: str) -> dict[str, Any]:
        """Generate embeddings for the given text.

        POST ``/api/embed``

        Parameters
        ----------
        model:
            Embedding model name.
        input_text:
            The text to embed.

        Returns
        -------
        dict containing ``embeddings`` key with the vector(s).
        """
        payload = {"model": model, "input": input_text}
        response = await self._request_with_retry("POST", "/api/embed", json_body=payload)
        return response.json()

    async def list_models(self) -> list[dict[str, Any]]:
        """List all locally available models.

        GET ``/api/tags``

        Returns
        -------
        List of model dicts, each with ``name``, ``size``, ``modified_at``, etc.
        """
        response = await self._request_with_retry("GET", "/api/tags")
        data = response.json()
        return data.get("models", [])

    async def show_model(self, model: str) -> dict[str, Any]:
        """Show details for a specific model.

        POST ``/api/show``

        Parameters
        ----------
        model:
            Model name to inspect.

        Returns
        -------
        Dict with model details (parameters, template, license, system prompt).
        """
        payload = {"name": model}
        response = await self._request_with_retry("POST", "/api/show", json_body=payload)
        return response.json()

    async def pull_model(
        self,
        model: str,
        stream: bool = True,
    ) -> AsyncIterator[dict[str, Any]]:
        """Pull a model from the Ollama registry.

        POST ``/api/pull``

        Parameters
        ----------
        model:
            Model name to pull (e.g. ``llama3.2``).
        stream:
            Stream progress updates (status, completed, total).  Defaults to True.

        Returns
        -------
        Async iterator of progress dicts when streaming; single dict otherwise.
        """
        payload: dict[str, Any] = {"name": model, "stream": stream}
        response = await self._request_with_retry("POST", "/api/pull", json_body=payload, stream=stream)

        if stream:
            return self._stream_response(response)
        return response.json()

    async def health_check(self) -> bool:
        """Check whether the Ollama server is reachable.

        Attempts GET ``/api/tags`` and returns True on success.
        """
        try:
            await self._request_with_retry("GET", "/api/tags")
            return True
        except OllamaError:
            return False

    async def get_version(self) -> str:
        """Return the Ollama server version string.

        GET ``/api/version``
        """
        response = await self._request_with_retry("GET", "/api/version")
        data = response.json()
        return data.get("version", "unknown")

    # -- model management ------------------------------------------------------

    async def create_model(
        self,
        model: str,
        modelfile: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Create a model from a Modelfile.

        POST ``/api/create``

        Parameters
        ----------
        model:
            Name for the new model.
        modelfile:
            Modelfile content. If None, the API reads from Modelfile in current directory.
        stream:
            If True, return an async iterator of progress updates.

        Returns
        -------
        Dict or async iterator with creation status/progress.
        """
        payload: dict[str, Any] = {"name": model, "stream": stream}
        if modelfile is not None:
            payload["modelfile"] = modelfile

        response = await self._request_with_retry("POST", "/api/create", json_body=payload, stream=stream)

        if stream:
            return self._stream_response(response)
        return response.json()

    async def delete_model(self, model: str) -> dict[str, Any]:
        """Delete a local model.

        DELETE ``/api/delete``

        Parameters
        ----------
        model:
            Model name to delete.

        Returns
        -------
        Dict with deletion status.
        """
        payload = {"name": model}
        response = await self._request_with_retry("DELETE", "/api/delete", json_body=payload)
        return response.json()

    async def copy_model(self, source: str, destination: str) -> dict[str, Any]:
        """Copy a local model.

        POST ``/api/copy``

        Parameters
        ----------
        source:
            Source model name.
        destination:
            Destination model name.

        Returns
        -------
        Dict with copy status.
        """
        payload = {"source": source, "destination": destination}
        response = await self._request_with_retry("POST", "/api/copy", json_body=payload)
        return response.json()

    async def list_running_models(self) -> list[dict[str, Any]]:
        """List currently running/loaded models.

        GET ``/api/ps``

        Returns
        -------
        List of running model dicts with name, size, etc.
        """
        response = await self._request_with_retry("GET", "/api/ps")
        data = response.json()
        return data.get("models", [])

    async def stop_model(self, model: str) -> dict[str, Any]:
        """Stop a running model.

        POST ``/api/generate`` (special use) or via session unload.

        Parameters
        ----------
        model:
            Model name to stop.

        Returns
        -------
        Dict with stop status.
        """
        payload = {"model": model, "keep_alive": 0}
        response = await self._request_with_retry("POST", "/api/generate", json_body=payload)
        return response.json()

    # -- OpenAI-compatible endpoint ------------------------------------------

    async def chat_openai(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Send a chat completion request via the OpenAI-compatible endpoint.

        POST ``/v1/chat/completions``

        Uses OpenAI-format request/response for compatibility with multi-provider
        routing.  The Ollama server translates this to its native format internally.

        Parameters
        ----------
        model:
            Model name.
        messages:
            Conversation as ``[{"role": "user", "content": "..."}]``.
        stream:
            If True, return an async iterator of SSE-style JSON chunks.
        **kwargs:
            Additional OpenAI-compatible parameters (``temperature``, ``max_tokens``, etc.).
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }

        response = await self._request_with_retry("POST", "/v1/chat/completions", json_body=payload, stream=stream)

        if stream:
            return self._stream_response(response)
        return response.json()

    # -- metrics extraction --------------------------------------------------

    @staticmethod
    def extract_metrics(response: dict[str, Any]) -> dict[str, Any]:
        """Extract token metrics from an Ollama API response.

        Pulls timing and token-count fields from the response dict and
        calculates derived metrics like tokens-per-second.

        Parameters
        ----------
        response:
            A non-streaming response dict from ``/api/chat`` or ``/api/generate``.

        Returns
        -------
        Dict with keys: ``prompt_eval_count``, ``eval_count``, ``total_duration``,
        ``load_duration``, ``prompt_eval_duration``, ``eval_duration``, and
        ``tokens_per_second``.
        """
        prompt_eval_count = response.get("prompt_eval_count", 0)
        eval_count = response.get("eval_count", 0)
        total_duration = response.get("total_duration", 0)
        load_duration = response.get("load_duration", 0)
        prompt_eval_duration = response.get("prompt_eval_duration", 0)
        eval_duration = response.get("eval_duration", 0)

        # Ollama reports durations in nanoseconds
        tokens_per_second = 0.0
        if eval_duration > 0:
            tokens_per_second = eval_count / (eval_duration / 1e9)

        return {
            "prompt_eval_count": prompt_eval_count,
            "eval_count": eval_count,
            "total_duration": total_duration,
            "load_duration": load_duration,
            "prompt_eval_duration": prompt_eval_duration,
            "eval_duration": eval_duration,
            "tokens_per_second": round(tokens_per_second, 2),
        }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    async def _test() -> None:
        client = OllamaClient()
        try:
            if await client.health_check():
                print("Ollama is running")
                version = await client.get_version()
                print(f"Version: {version}")
                models = await client.list_models()
                print(f"Models: {[m['name'] for m in models]}")
            else:
                print("Ollama is not running")
        finally:
            await client.close()

    asyncio.run(_test())
