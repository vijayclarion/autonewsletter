"""Citation extraction and validation (FR-010, constitution Principle III).

Writers must mark every factual statement with ``[C:chunk-id]``. This module turns those
markers into numbered anchors, validates each id against the chunks actually supplied,
and reports sections whose support is insufficient.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_MARKER_RE = re.compile(r"\s*\[C:([0-9a-fA-F-]{8,})\]")
_SHORT_MARKER_RE = re.compile(r"\[C:\s*([^\]]+?)\s*\]")


def expand_short_markers(body_md: str, short_to_id: dict[str, str]) -> str:
    """Rewrite ``[C:<short>]`` markers to ``[C:<full-chunk-id>]``.

    Writers are handed compact ids (``0``, ``1``, …) because, given full UUIDs, models
    abbreviate them in citation markers and the truncated ids fail validation. Markers
    whose id is unknown are left untouched so :func:`extract` still reports them invalid.
    """

    def _swap(match: re.Match) -> str:
        full = short_to_id.get(match.group(1))
        return f"[C:{full}]" if full else match.group(0)

    return _SHORT_MARKER_RE.sub(_swap, body_md)


@dataclass
class ExtractedCitation:
    anchor: str               # e.g. "c1" — stable anchor within the section body
    chunk_ids: list[str]


@dataclass
class CitationExtraction:
    body_md: str              # markers replaced with [anchor] references
    citations: list[ExtractedCitation] = field(default_factory=list)
    invalid_ids: list[str] = field(default_factory=list)
    insufficient_support: bool = False


def extract(body_md: str, valid_chunk_ids: set[str]) -> CitationExtraction:
    """Replace consecutive ``[C:id]`` markers with one numbered anchor per statement."""
    citations: list[ExtractedCitation] = []
    invalid: list[str] = []
    pending: list[str] = []
    output: list[str] = []
    cursor = 0

    def flush(position: int) -> None:
        nonlocal pending
        if pending:
            anchor = f"c{len(citations) + 1}"
            citations.append(ExtractedCitation(anchor=anchor, chunk_ids=pending))
            output.append(f" [{anchor}]")
            pending = []

    for match in _MARKER_RE.finditer(body_md):
        between = body_md[cursor : match.start()]
        if between.strip():
            flush(cursor)
        output.append(between)
        chunk_id = match.group(1)
        if chunk_id in valid_chunk_ids:
            if chunk_id not in pending:
                pending.append(chunk_id)
        else:
            invalid.append(chunk_id)
        cursor = match.end()

    flush(cursor)
    output.append(body_md[cursor:])

    return CitationExtraction(
        body_md="".join(output).strip(),
        citations=citations,
        invalid_ids=invalid,
        insufficient_support=len(citations) == 0,
    )
