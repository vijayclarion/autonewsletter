#!/usr/bin/env python3
"""
LLM Configuration Module
Centralized LLM initialization with support for multiple providers via LangChain.

Provider selection is driven by the LLM_PROVIDER environment variable:
  - openai   (default) – uses ChatOpenAI
  - anthropic / claude  – uses ChatAnthropic
  - ollama              – uses ChatOllama (local models)

Relevant environment variables:
  LLM_PROVIDER        openai | anthropic | claude | ollama
  LLM_MODEL           model name (e.g. gpt-4o-mini, claude-3-haiku-20240307)
  OPENAI_API_KEY      API key for OpenAI
  ANTHROPIC_API_KEY   API key for Anthropic / Claude
  OLLAMA_BASE_URL     Base URL for Ollama (default: http://localhost:11434)
  OLLAMA_MODEL        Model name for Ollama (default: llama2)
"""

import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> BaseChatModel:
    """
    Return a LangChain chat model configured for the requested provider.

    Args:
        provider:    LLM provider name.  Defaults to the LLM_PROVIDER env var,
                     falling back to 'openai'.
        model:       Model identifier.  Defaults to the LLM_MODEL env var.
        temperature: Sampling temperature (0.0 – 1.0).
        max_tokens:  Maximum tokens to generate in a single response.

    Returns:
        A ``BaseChatModel`` instance ready to use with LangChain chains or
        direct ``.invoke()`` calls.

    Raises:
        ValueError: If the requested provider is not supported.
        ImportError: If the required LangChain provider package is not installed.
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "openai")
    provider = provider.lower()

    if provider == "openai":
        resolved_model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        api_key = os.environ.get("OPENAI_API_KEY", "api_key_placeholder")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is required for the OpenAI provider. "
                "Install it with: pip install langchain-openai"
            ) from exc
        return ChatOpenAI(
            model=resolved_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    if provider in ("anthropic", "claude"):
        resolved_model = model or os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "api_key_placeholder")
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise ImportError(
                "langchain-anthropic is required for the Anthropic/Claude provider. "
                "Install it with: pip install langchain-anthropic"
            ) from exc
        return ChatAnthropic(
            model=resolved_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    if provider == "ollama":
        resolved_model = model or os.environ.get("OLLAMA_MODEL", "llama2")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError as exc:
            raise ImportError(
                "langchain-community is required for the Ollama provider. "
                "Install it with: pip install langchain-community"
            ) from exc
        return ChatOllama(
            model=resolved_model,
            base_url=base_url,
            temperature=temperature,
        )

    raise ValueError(
        f"Unsupported LLM provider: '{provider}'. "
        "Supported providers: openai, anthropic, claude, ollama."
    )
