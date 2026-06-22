"""Anthropic adapter — the only module in the codebase that imports the Anthropic SDK."""

from __future__ import annotations

import os

import anthropic

from newsletter_engine.config import ProviderConfig
from newsletter_engine.models.provider import ChatResult, EmbedResult, ModelCallError

_MAX_TOKENS = 8192
_JSON_SYSTEM_SUFFIX = (
    "Respond with a single valid JSON object only — no prose, no markdown fences."
)


def _extract_json(text: str) -> str:
    """Best-effort isolation of the JSON object in a response (no native JSON mode)."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]
    return stripped


class AnthropicAdapter:
    name = "anthropic"

    def __init__(self, provider_config: ProviderConfig):
        key_env = provider_config.api_key_env or "ANTHROPIC_API_KEY"
        api_key = os.environ.get(key_env)
        if not api_key:
            raise ModelCallError(
                f"Environment variable {key_env} is not set; cannot use the Anthropic provider"
            )
        self._client = anthropic.Anthropic(api_key=api_key)

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        # Anthropic takes the system prompt as a parameter, not a message.
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        if json_mode:
            system_parts.append(_JSON_SYSTEM_SUFFIX)
        chat_messages = [m for m in messages if m["role"] != "system"]
        if not chat_messages:
            chat_messages = [{"role": "user", "content": "Proceed."}]

        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=_MAX_TOKENS,
                temperature=temperature,
                system="\n\n".join(system_parts) or anthropic.NOT_GIVEN,
                messages=chat_messages,
            )
        except (
            anthropic.RateLimitError,
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
            anthropic.InternalServerError,
        ) as exc:
            raise ModelCallError(str(exc), retryable=True) from exc
        except anthropic.AnthropicError as exc:
            raise ModelCallError(str(exc), retryable=False) from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        if json_mode:
            text = _extract_json(text)
        usage = response.usage
        return ChatResult(
            text=text,
            model=model,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
        )

    def embed(self, model: str, texts: list[str]) -> EmbedResult:
        raise ModelCallError(
            "Anthropic offers no embedding API; route the 'embedder' role to the"
            " 'local' provider (see config/models.yaml)"
        )
