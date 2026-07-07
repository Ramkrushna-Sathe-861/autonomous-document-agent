"""
LLM client wrapper for Groq API (OpenAI-compatible).

Purpose: Encapsulate all LLM interactions with retry logic and error handling.
Responsibility: Manage API calls, handle timeouts, parse responses, and retry logic.
"""

import json
import logging
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

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Groq API error: {response.status_code} - {response.text}"
                    )
                    raise LLMError(
                        f"Groq API returned status {response.status_code}"
                    )

                data = response.json()
                completion = data["choices"][0]["message"]["content"]
                logger.debug(f"LLM completion generated: {len(completion)} chars")
                return completion

        except httpx.TimeoutException as e:
            logger.error(f"Groq API timeout: {str(e)}")
            raise LLMError(f"LLM API timeout after {self.timeout}s") from e
        except httpx.RequestError as e:
            logger.error(f"Groq API request error: {str(e)}")
            raise LLMError(f"LLM API request failed: {str(e)}") from e
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Groq API response parsing error: {str(e)}")
            raise LLMError(f"Failed to parse LLM response: {str(e)}") from e

    async def structured_complete(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
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

        try:
            async with httpx.AsyncClient() as client:
                request_body = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": {
                        "type": "json_object",
                    },
                }

                if response_format:
                    request_body["response_format"]["schema"] = response_format

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_body,
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Groq API error: {response.status_code} - {response.text}"
                    )
                    raise LLMError(
                        f"Groq API returned status {response.status_code}"
                    )

                data = response.json()
                completion = data["choices"][0]["message"]["content"]
                parsed = json.loads(completion)

                logger.debug(f"Structured LLM response generated")
                return parsed

        except httpx.TimeoutException as e:
            logger.error(f"Groq API timeout: {str(e)}")
            raise LLMError(f"LLM API timeout after {self.timeout}s") from e
        except httpx.RequestError as e:
            logger.error(f"Groq API request error: {str(e)}")
            raise LLMError(f"LLM API request failed: {str(e)}") from e
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Groq API response parsing error: {str(e)}")
            raise LLMError(f"Failed to parse LLM response: {str(e)}") from e
