"""Citation tracing: citation id -> source file, location, supporting excerpt (FR-021)."""

from __future__ import annotations

import json

from newsletter_engine.store.db import Database

_EXCERPT_CHARS = 400


class TraceError(Exception):
    """Citation cannot be resolved for the given edition."""


def trace_citation(db: Database, month: str, citation_id: str) -> dict:
    citation = db.get_citation(citation_id)
    if citation is None:
        raise TraceError(f"No citation with id '{citation_id}'")

    section = db.get_section(citation["section_id"])
    if section is None or section["edition_id"] != month:
        raise TraceError(f"Citation '{citation_id}' does not belong to edition {month}")

    supports = []
    for chunk_id in json.loads(citation["chunk_ids"]):
        chunk = db.get_chunk(chunk_id)
        if chunk is None:
            supports.append({"chunk_id": chunk_id, "error": "chunk no longer exists"})
            continue
        source = db.get_source(chunk["source_id"])
        supports.append(
            {
                "chunk_id": chunk_id,
                "file": source["path"],
                "input_type": source["input_type"],
                "location": json.loads(chunk["location"]),
                "excerpt": chunk["text"][:_EXCERPT_CHARS],
            }
        )

    return {
        "citation_id": citation_id,
        "anchor": citation["statement_anchor"],
        "section": section["title"],
        "supports": supports,
    }
