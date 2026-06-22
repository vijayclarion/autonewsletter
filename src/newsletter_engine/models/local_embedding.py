"""Local embedding provider: ChromaDB's built-in ONNX MiniLM, no API key, no network egress.

Content embedded here never leaves the machine (research R4/R13); the model file is
downloaded once by chromadb on first use.
"""

from __future__ import annotations

from newsletter_engine.config import ProviderConfig
from newsletter_engine.models.provider import ChatResult, EmbedResult, ModelCallError


class LocalEmbeddingAdapter:
    name = "local"

    def __init__(self, provider_config: ProviderConfig):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._embed_fn = DefaultEmbeddingFunction()

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        raise ModelCallError("The 'local' provider only supports the embedder role")

    def embed(self, model: str, texts: list[str]) -> EmbedResult:
        try:
            vectors = self._embed_fn(texts)
        except Exception as exc:  # onnxruntime/model-download failures
            raise ModelCallError(f"local embedding failed: {exc}", retryable=False) from exc
        return EmbedResult(
            vectors=[[float(v) for v in vector] for vector in vectors],
            model=model,
            input_tokens=0,
        )
