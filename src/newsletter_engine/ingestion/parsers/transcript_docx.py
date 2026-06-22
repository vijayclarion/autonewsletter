"""Teams-style meeting transcript (.docx) parser.

Detects the Teams transcript export structure — speaker + timestamp header paragraphs —
and chunks by speaker turn with timestamp provenance (FR-002/FR-003).
"""

from __future__ import annotations

import re

import docx

from newsletter_engine.ingestion.chunker import ParsedChunk

# "Jane Doe   0:05" / "Jane Doe 1:02:33" — header paragraph ending in a timestamp
_HEADER_RE = re.compile(
    r"^(?P<speaker>[^\d\n][^\n]{0,80}?)\s+(?P<ts>\d{1,2}:\d{2}(?::\d{2})?)\s*$"
)
# Bare timestamp paragraph variants ("0:05" or "00:00:05.000 --> 00:00:08.000")
_BARE_TS_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:\s*-->.*)?$")

_MIN_HEADER_MATCHES = 3


def _paragraph_texts(path) -> list[str]:
    """Logical lines: Teams exports may pack 'Speaker  0:03\\nUtterance' into one
    paragraph with embedded newlines, so paragraphs are split into lines first."""
    document = docx.Document(str(path))
    lines: list[str] = []
    for paragraph in document.paragraphs:
        for line in paragraph.text.splitlines():
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def looks_like_transcript(path) -> bool:
    """Transcript-vs-document sniffing for .docx (FR-002a)."""
    try:
        texts = _paragraph_texts(path)
    except Exception:
        return False
    hits = sum(1 for t in texts if _HEADER_RE.match(t) or _BARE_TS_RE.match(t))
    return hits >= _MIN_HEADER_MATCHES


def parse(path) -> list[ParsedChunk]:
    """Chunk by speaker turn; consecutive turns by the same speaker are merged."""
    texts = _paragraph_texts(path)
    chunks: list[ParsedChunk] = []
    speaker: str | None = None
    timestamp: str | None = None
    buffer: list[str] = []

    def flush():
        nonlocal buffer
        if buffer:
            chunks.append(
                ParsedChunk(
                    text=" ".join(buffer),
                    location={
                        "timestamp": timestamp or "",
                        "speaker": speaker or "Unknown Speaker",
                    },
                )
            )
            buffer = []

    for text in texts:
        header = _HEADER_RE.match(text)
        if header:
            new_speaker = header.group("speaker").strip()
            if new_speaker != speaker:
                flush()
                speaker = new_speaker
                timestamp = header.group("ts")
            elif timestamp is None:
                timestamp = header.group("ts")
            continue
        if _BARE_TS_RE.match(text):
            if timestamp is None:
                timestamp = text.split("-->")[0].strip()
            continue
        buffer.append(text)

    flush()
    return chunks
