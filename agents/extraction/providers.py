"""
Provider abstraction layer for Agent 1.
Decouples domain logic from specific LLM vendor SDKs per architecture rule #10.
"""

from typing import Any, Callable, Dict, Optional, Protocol
import httpx

from agents.extraction.exceptions import ProviderUnavailableError


class LLMProvider(Protocol):
    """
    Abstract interface for LLM extraction providers.
    """
    async def generate_extraction(self, prompt: str, system_prompt: str) -> str:
        """
        Sends trusted instructions and untrusted prompt to the model and returns raw response string.
        """
        ...


class MockDeterministicProvider:
    """
    Deterministic provider implementation for unit tests, offline development,
    and reproducible synthetic demos.
    """
    def __init__(
        self,
        canned_response: Optional[str] = None,
        response_factory: Optional[Callable[[str, str], str]] = None,
        should_fail: bool = False,
        failure_exception: Optional[Exception] = None,
    ):
        self.canned_response = canned_response or "{}"
        self.response_factory = response_factory
        self.should_fail = should_fail
        self.failure_exception = failure_exception or ProviderUnavailableError("Mock provider simulated outage.")
        self.call_count = 0
        self.last_prompt: Optional[str] = None
        self.last_system_prompt: Optional[str] = None

    async def generate_extraction(self, prompt: str, system_prompt: str) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt

        if self.should_fail:
            raise self.failure_exception

        if self.response_factory:
            return self.response_factory(prompt, system_prompt)

        return self.canned_response


class GenericHTTPProvider:
    """
    Lightweight, vendor-neutral HTTP adapter for OpenAI-compatible or gateway endpoints.
    Uses httpx without importing any proprietary vendor SDK.
    """
    def __init__(
        self,
        endpoint_url: str,
        api_key: Optional[str] = None,
        model_name: str = "default-extraction-model",
        timeout_seconds: float = 30.0,
    ):
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout_seconds

    async def generate_extraction(self, prompt: str, system_prompt: str) -> str:
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint_url, json=payload, headers=headers)
                if response.status_code != 200:
                    raise ProviderUnavailableError(
                        f"Provider returned HTTP {response.status_code}: {response.text[:200]}"
                    )
                data = response.json()
                # Support standard chat completion output
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "")
                # Support direct text response
                if "response" in data:
                    return str(data["response"])
                raise ProviderUnavailableError("Unrecognized HTTP provider response format.")
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"HTTP request to model provider failed: {exc}") from exc
        except Exception as exc:
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError(f"Provider invocation error: {exc}") from exc
