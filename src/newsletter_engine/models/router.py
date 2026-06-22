"""Role -> provider/model routing with retries, logging, and cost tracking.

No provider SDK imports here (constitution Principle I); adapters are resolved lazily by
name from the registry below.
"""

from __future__ import annotations

import importlib
import time

from newsletter_engine.config import ModelsConfig, ProviderConfig
from newsletter_engine.models.provider import (
    ChatResult,
    EmbedResult,
    ModelCallError,
    ModelProvider,
)

# provider name -> "module:Class" of its adapter (the only place SDKs get imported)
ADAPTER_REGISTRY: dict[str, str] = {
    "anthropic": "newsletter_engine.models.anthropic_adapter:AnthropicAdapter",
    "openai": "newsletter_engine.models.openai_adapter:OpenAIAdapter",
    "local": "newsletter_engine.models.local_embedding:LocalEmbeddingAdapter",
    "mock": "newsletter_engine.models.mock_adapter:MockAdapter",
}

_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 2.0


class ModelRouter:
    """Routes logical roles (classifier/writer/diagrammer/embedder) to providers."""

    def __init__(self, models_config: ModelsConfig, *, log=None, cost_tracker=None):
        self._config = models_config
        self._log = log
        self._cost = cost_tracker
        self._providers: dict[str, ModelProvider] = {}

    def _provider(self, name: str) -> ModelProvider:
        if name not in self._providers:
            spec = ADAPTER_REGISTRY.get(name)
            if spec is None:
                raise ModelCallError(f"No adapter registered for provider '{name}'")
            module_name, class_name = spec.split(":")
            cls = getattr(importlib.import_module(module_name), class_name)
            provider_config = self._config.providers.get(name, ProviderConfig())
            self._providers[name] = cls(provider_config)
        return self._providers[name]

    def _route(self, role: str):
        route = self._config.roles.get(role)
        if route is None:
            raise ModelCallError(f"No route configured for role '{role}'")
        return self._provider(route.provider), route

    def chat(
        self,
        role: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        provider, route = self._route(role)
        result = self._with_retries(
            role,
            route,
            lambda: provider.chat(
                route.model, messages, temperature=temperature, json_mode=json_mode
            ),
        )
        self._record(role, route, result.input_tokens, result.output_tokens)
        return result

    def embed(self, role: str, texts: list[str]) -> EmbedResult:
        provider, route = self._route(role)
        result = self._with_retries(role, route, lambda: provider.embed(route.model, texts))
        self._record(role, route, result.input_tokens, 0)
        return result

    def _with_retries(self, role: str, route, call):
        start = time.monotonic()
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                result = call()
                if self._log:
                    self._log.info(
                        "model_call",
                        role=role,
                        provider=route.provider,
                        model=route.model,
                        attempt=attempt,
                        latency_ms=round((time.monotonic() - start) * 1000),
                    )
                return result
            except ModelCallError as exc:
                if self._log:
                    self._log.warning(
                        "model_call_failed",
                        role=role,
                        provider=route.provider,
                        model=route.model,
                        attempt=attempt,
                        retryable=exc.retryable,
                        error=str(exc),
                    )
                if not exc.retryable or attempt == _MAX_ATTEMPTS:
                    raise
                time.sleep(_BACKOFF_SECONDS * attempt)
        raise ModelCallError(f"model call for role '{role}' exhausted retries")  # unreachable

    def _record(self, role: str, route, input_tokens: int, output_tokens: int) -> None:
        if self._cost:
            self._cost.record(route.model, input_tokens, output_tokens)
        if self._log:
            self._log.info(
                "model_usage",
                role=role,
                model=route.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
