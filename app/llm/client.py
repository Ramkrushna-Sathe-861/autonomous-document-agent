"""
LLM client wrapper for Groq API (OpenAI-compatible).

Purpose: Encapsulate all LLM interactions with retry logic and error handling.
Responsibility: Manage API calls, handle timeouts, parse responses, and retry logic.
"""

import json
import logging
import asyncio
from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq API client with retry logic and structured output support."""

    def __init__(self):
        """Initialize Groq client with settings."""
        self.settings = get_settings()
        self.base_url = "https://api.groq.com/openai/v1"
        self.api_key = self.settings.groq_api_key
        self.model = self.settings.groq_model
        self.timeout = self.settings.groq_timeout
        self.max_retries = self.settings.groq_max_retries

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str | None = None,
    ) -> str:
        """
        Get completion from Groq API.

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Generated text completion

        Raises:
            LLMError: If API call fails
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        return await self._request(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            structured=False,
        )

    async def _request(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        model: str | None,
        structured: bool,
    ) -> Any:
        """Send a completion request with bounded exponential-backoff retries."""
        if not self.api_key:
            raise LLMError("GROQ_API_KEY is not configured")

        body: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if structured:
            body["response_format"] = {"type": "json_object"}

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                        json=body,
                )
                    if response.status_code in {429, 500, 502, 503, 504}:
                        last_error = LLMError(
                            f"Groq API temporarily unavailable ({response.status_code})"
                        )
                        if attempt == self.max_retries:
                            break
                        retry_after = response.headers.get("Retry-After")
                        delay = 0.5 * (2 ** (attempt - 1))
                        if retry_after:
                            try:
                                delay = max(delay, float(retry_after))
                            except ValueError:
                                pass
                        logger.warning(
                            "Groq request failed with %s on attempt %s/%s; retrying in %.2fs",
                            response.status_code,
                            attempt,
                            self.max_retries,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    if response.status_code != 200:
                        raise LLMError(f"Groq API returned status {response.status_code}: {response.text[:200]}")
                    content = response.json()["choices"][0]["message"]["content"]
                    return json.loads(content) if structured else content
                except (httpx.TimeoutException, httpx.RequestError, LLMError) as exc:
                    last_error = exc
                    if attempt == self.max_retries:
                        break
                    logger.warning("LLM attempt %s/%s failed: %s", attempt, self.max_retries, exc)
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                except (KeyError, json.JSONDecodeError) as exc:
                    raise LLMError(f"Failed to parse LLM response: {exc}") from exc
        raise LLMError(f"LLM request failed after {self.max_retries} attempts: {last_error}") from last_error

    async def structured_complete(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Get structured JSON completion from Groq API.

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            response_format: JSON schema for structured output
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If API call or parsing fails
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        # Groq's JSON mode guarantees valid JSON. The schema is included in the
        # prompt by callers because the OpenAI-compatible endpoint does not accept
        # a custom `schema` member in response_format.
        return await self._request(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            structured=True,
        )
