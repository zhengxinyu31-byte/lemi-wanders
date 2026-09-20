"""Minimal LLM HTTP client (OpenAI-compatible chat completions).

Credentials come from environment variables; every request carries a
timeout. An http_post callable can be injected for offline testing.
"""
from __future__ import annotations

import os
from typing import Callable, Optional

DEFAULT_TIMEOUT = 120


class LLMError(Exception):
    """Raised when an LLM request fails or returns an unusable response."""


class LLMClient:
    """OpenAI-compatible chat client with injectable transport."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None, timeout: Optional[int] = None,
                 http_post: Optional[Callable] = None) -> None:
        self.api_key = api_key or ""
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or ""
        self.timeout = timeout or DEFAULT_TIMEOUT
        self._http_post = http_post

    @classmethod
    def from_env(cls) -> "LLMClient":
        """Build a client from LLM_* environment variables."""
        return cls(
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", "https://api.minimaxi.com/v1"),
            model=os.getenv("LLM_MODEL_ID", "MiniMax-M3"),
            timeout=int(os.getenv("LLM_TIMEOUT", str(DEFAULT_TIMEOUT))),
        )

    def _post(self):
        if self._http_post is not None:
            return self._http_post
        import requests  # local import so tests don't require the dep
        return requests.post

    def complete(self, system: str, user: str) -> str:
        """Return the assistant text for a system+user prompt.

        Raises:
            LLMError: on network failure or malformed response.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        payload = {"model": self.model,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]}
        try:
            resp = self._post()(url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # process-boundary catch: wrap, never swallow
            raise LLMError(str(exc)) from exc
