"""Deterministic offline adapter for fixture dry runs (constitution Principle V).

Sends nothing anywhere: classification is keyword-based, generation is templated from the
provided chunks, embeddings are content hashes. Allow-listing ``mock`` in a dry-run
models.yaml lets the full pipeline execute without credentials or network access.
"""

from __future__ import annotations

import hashlib
import json
import re

from newsletter_engine.config import ProviderConfig
from newsletter_engine.models.provider import ChatResult, EmbedResult

_TECH_WORDS = re.compile(
    r"\b(api|architecture|gateway|deploy|database|cach\w*|latency|service|pipeline|"
    r"kubernetes|docker|security|code|migration|design|infra\w*|model|endpoint|schema|"
    r"queue|token|throughput|backend|frontend|cloud|azure|aws|sdk|cli|refactor|bug|"
    r"release|integration|vector|embedding|llm|rag|sprint|repository|microservice)\b",
    re.IGNORECASE,
)


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


class MockAdapter:
    name = "mock"

    def __init__(self, provider_config: ProviderConfig):
        self._config = provider_config

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        text = self._respond(system, user)
        return ChatResult(
            text=text,
            model=model,
            input_tokens=_tokens(system + user),
            output_tokens=_tokens(text),
        )

    def _respond(self, system: str, user: str) -> str:
        payload = self._json_payload(user)
        if "content classifier" in system:
            return self._classify(payload)
        if "group" in system.lower() and "topics" in system.lower():
            return self._topics(payload)
        if "writing a story" in system:
            return self._story(payload)
        if "TL;DR" in system:
            return json.dumps(
                {"body_md": "- The team advanced its key technical initiatives this month."}
            )
        if "action items" in system.lower():
            return json.dumps(
                {"body_md": "- **Solution Architect**: follow up on the open design decisions."}
            )
        if "Mermaid" in system and "alt text" not in system.lower():
            return json.dumps(
                {
                    "needed": True,
                    "mermaid": (
                        'flowchart LR\n  A["Source Content"] --> B["Processing Pipeline"]\n'
                        '  B --> C["Newsletter Draft"]'
                    ),
                    "caption": "High-level flow from source content to the newsletter draft.",
                }
            )
        if "alt text" in system.lower():
            return json.dumps(
                {
                    "alt_text": (
                        "Source content flows into a processing pipeline, which produces "
                        "the newsletter draft."
                    )
                }
            )
        return json.dumps({"body_md": "Mock response."})

    @staticmethod
    def _json_payload(user: str) -> dict:
        try:
            return json.loads(user)
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def _classify(payload: dict) -> str:
        results = []
        for chunk in payload.get("chunks", []):
            hits = len(_TECH_WORDS.findall(chunk.get("text", "")))
            if hits >= 2:
                results.append(
                    {"index": chunk["index"], "label": "technical", "confidence": 0.95}
                )
            elif hits == 1:
                results.append(
                    {"index": chunk["index"], "label": "technical", "confidence": 0.85}
                )
            else:
                results.append(
                    {"index": chunk["index"], "label": "non_technical", "confidence": 0.9}
                )
        return json.dumps({"results": results})

    @staticmethod
    def _topics(payload: dict) -> str:
        ids = [c["id"] for c in payload.get("chunks", [])]
        return json.dumps(
            {"topics": [{"title": "This Month in Engineering", "chunk_ids": ids}]}
        )

    @staticmethod
    def _story(payload: dict) -> str:
        chunks = payload.get("chunks", [])
        if not chunks:
            return json.dumps({"insufficient_support": True})
        paragraphs = []
        for chunk in chunks[:6]:
            sentence = chunk.get("text", "").strip().split(". ")[0][:300]
            paragraphs.append(f"{sentence}. [C:{chunk['id']}]")
        return json.dumps(
            {"title": payload.get("topic", "Engineering Update"), "body_md": "\n\n".join(paragraphs)}
        )

    def embed(self, model: str, texts: list[str]) -> EmbedResult:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append([b / 255.0 for b in digest])  # 32-dim deterministic vector
        return EmbedResult(
            vectors=vectors, model=model, input_tokens=sum(_tokens(t) for t in texts)
        )
