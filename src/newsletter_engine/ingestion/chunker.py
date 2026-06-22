"""Normalized ContentChunk emission (constitution Principle II).

Every parser emits ``ParsedChunk``s; the chunker turns them into ``ContentChunk`` dicts
with stable ids and ordinals, ready for persistence and classification.
"""

from __future__ import annotations

from dataclasses import dataclass

from newsletter_engine.store.db import new_id

MIN_CHUNK_CHARS = 20  # noise floor: drop fragments too short to classify or cite


@dataclass
class ParsedChunk:
    text: str
    location: dict


def to_content_chunks(source_id: str, parsed: list[ParsedChunk]) -> list[dict]:
    chunks = []
    ordinal = 0
    for piece in parsed:
        text = piece.text.strip()
        if len(text) < MIN_CHUNK_CHARS:
            continue
        chunks.append(
            {
                "id": new_id(),
                "source_id": source_id,
                "ordinal": ordinal,
                "text": text,
                "location": piece.location,
                "label": None,
                "label_confidence": None,
                "eligible": False,
            }
        )
        ordinal += 1
    return chunks
