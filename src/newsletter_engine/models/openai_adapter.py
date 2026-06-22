"""OpenAI adapter — the only module in the codebase that imports the OpenAI SDK."""

from __future__ import annotations

import os

import openai

from newsletter_engine.config import ProviderConfig
from newsletter_engine.models.provider import ChatResult, EmbedResult, ModelCallError


class OpenAIAdapter:
    name = "openai"

    def __init__(self, provider_config: ProviderConfig):
        key_env = provider_config.api_key_env or "OPENAI_API_KEY"
        api_key = os.environ.get(key_env)
        if not api_key:
            raise ModelCallError(
                f"Environment variable {key_env} is not set; cannot use the OpenAI provider"
            )
        self._client = openai.OpenAI(api_key=api_key)

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        kwargs: dict = {"model": model, "messages": messages, "temperature": temperature}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self._client.chat.completions.create(**kwargs)
        except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as exc:
            raise ModelCallError(str(exc), retryable=True) from exc
        except openai.InternalServerError as exc:
            raise ModelCallError(str(exc), retryable=True) from exc
        except openai.OpenAIError as exc:
            raise ModelCallError(str(exc), retryable=False) from exc

        usage = response.usage
        return ChatResult(
            text=response.choices[0].message.content or "",
            model=model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

    def embed(self, model: str, texts: list[str]) -> EmbedResult:
        try:
            response = self._client.embeddings.create(model=model, input=texts)
        except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as exc:
            raise ModelCallError(str(exc), retryable=True) from exc
        except openai.InternalServerError as exc:
            raise ModelCallError(str(exc), retryable=True) from exc
        except openai.OpenAIError as exc:
            raise ModelCallError(str(exc), retryable=False) from exc

        return EmbedResult(
            vectors=[item.embedding for item in response.data],
            model=model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
        )
