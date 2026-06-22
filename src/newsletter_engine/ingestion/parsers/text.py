"""Plain text / markdown parser: paragraph chunks with line-range provenance."""

from __future__ import annotations

from pathlib import Path

from newsletter_engine.ingestion.chunker import ParsedChunk


def parse(path) -> list[ParsedChunk]:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    chunks: list[ParsedChunk] = []
    buffer: list[str] = []
    start_line = 1

    def flush(end_line: int):
        nonlocal buffer
        if buffer:
            chunks.append(
                ParsedChunk(
                    text="\n".join(buffer), location={"lines": f"{start_line}-{end_line}"}
                )
            )
            buffer = []

    for number, line in enumerate(lines, start=1):
        if line.strip():
            if not buffer:
                start_line = number
            buffer.append(line.rstrip())
        else:
            flush(number - 1)

    flush(len(lines))
    return chunks
