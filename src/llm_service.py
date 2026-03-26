#!/usr/bin/env python3
"""
LLM Service Module
Unified interface for all LLM operations, built on top of the LangChain
abstraction layer provided by ``llm_config.get_llm()``.

Usage::

    from llm_service import LLMService

    # Initialise (provider/model resolved from environment variables)
    service = LLMService()

    # Plain-text generation
    text = service.generate(
        prompt="Summarise this content in three bullets.",
        system_prompt="You are a concise technical writer.",
        temperature=0.3,
        max_tokens=300,
    )

    # Structured generation (returns a Pydantic model instance)
    from pydantic import BaseModel
    class Summary(BaseModel):
        title: str
        key_points: list[str]

    result = service.generate_structured(
        prompt="Extract the summary from the text below.\\n\\n...",
        output_model=Summary,
    )
    print(result.title)
"""

import os
from typing import Optional, Type, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from llm_config import get_llm

T = TypeVar("T")

_DEFAULT_SYSTEM_PROMPT = (
    "You are an expert enterprise technology analyst and strategic content writer."
)


class LLMService:
    """
    Provider-agnostic LLM service built on LangChain.

    A single instance can be shared across the application.  The underlying
    model is initialised once from environment variables and reused for all
    calls.  Per-call overrides for temperature and max_tokens are applied
    with LangChain's ``.bind()`` mechanism, so no extra model instances are
    created unnecessarily.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> None:
        """
        Initialize the service.

        Args:
            provider:    Override the LLM_PROVIDER env var.
            model:       Override the LLM_MODEL env var.
            temperature: Default sampling temperature.
            max_tokens:  Default maximum tokens per response.
        """
        self._default_temperature = temperature
        self._default_max_tokens = max_tokens
        self.llm: Optional[BaseChatModel] = None
        self.llm_available: bool = False

        try:
            self.llm = get_llm(
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            self.llm_available = True
            provider_name = provider or os.environ.get("LLM_PROVIDER", "openai")
            model_name = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
            print(f"✓ LLM initialised: {provider_name} ({model_name})")
        except Exception as exc:
            print(f"⚠ LLM initialisation failed: {exc}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a text response for *prompt*.

        Args:
            prompt:        The user-facing prompt.
            system_prompt: Optional system / instruction message.
            temperature:   Override the default sampling temperature.
            max_tokens:    Override the default token limit.

        Returns:
            The model's text response, or an empty string if the LLM is
            unavailable or an error occurs.
        """
        if not self.llm_available or self.llm is None:
            return ""

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = self._get_llm_with_overrides(temperature, max_tokens)
        try:
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as exc:
            print(f"⚠ LLM generation failed: {exc}")
            return ""

    def generate_structured(
        self,
        prompt: str,
        output_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[T]:
        """
        Generate a structured response parsed into *output_model*.

        Uses LangChain's ``with_structured_output`` to bind the Pydantic
        model to the LLM so that the response is automatically validated and
        parsed.

        Args:
            prompt:        The user-facing prompt.
            output_model:  A Pydantic ``BaseModel`` subclass describing the
                           expected output schema.
            system_prompt: Optional system / instruction message.
            temperature:   Override the default sampling temperature.
            max_tokens:    Override the default token limit.

        Returns:
            A populated instance of *output_model*, or ``None`` on failure.
        """
        if not self.llm_available or self.llm is None:
            return None

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = self._get_llm_with_overrides(temperature, max_tokens)
        try:
            structured_llm = llm.with_structured_output(output_model)
            return structured_llm.invoke(messages)
        except Exception as exc:
            print(f"⚠ Structured LLM generation failed: {exc}")
            return None

    def generate_batch(
        self,
        prompts: list,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> list:
        """
        Generate text responses for a list of prompts.

        Args:
            prompts:       List of user-facing prompt strings.
            system_prompt: Shared system message applied to every prompt.
            temperature:   Override the default sampling temperature.
            max_tokens:    Override the default token limit.

        Returns:
            List of response strings (empty string for any failed call).
        """
        return [
            self.generate(p, system_prompt=system_prompt,
                          temperature=temperature, max_tokens=max_tokens)
            for p in prompts
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_llm_with_overrides(
        self,
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> BaseChatModel:
        """Return the LLM, binding per-call parameter overrides if required."""
        overrides = {}
        if temperature is not None and temperature != self._default_temperature:
            overrides["temperature"] = temperature
        if max_tokens is not None and max_tokens != self._default_max_tokens:
            overrides["max_tokens"] = max_tokens

        if overrides:
            return self.llm.bind(**overrides)
        return self.llm
