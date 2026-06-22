"""Provider-agnostic model interface (constitution Principle I).

This module and router.py must never import a provider SDK; adapters own that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ChatResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


@dataclass
class EmbedResult:
    vectors: list[list[float]]
    model: str
    input_tokens: int


class ModelCallError(Exception):
    """Error envelope for adapter failures.

    ``retryable`` distinguishes transient faults (rate limits, timeouts, 5xx) the router
    may retry from permanent ones (auth, bad request) it must surface immediately.
    """

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


@runtime_checkable
class ModelProvider(Protocol):
    """Contract every provider adapter implements."""

    name: str

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult: ...

    def embed(self, model: str, texts: list[str]) -> EmbedResult: ...
