"""Recursive source scan, input-type detection, and skip-and-report ingestion (FR-001–FR-004).

Malformed or unsupported files never abort the run: they are recorded as ``skipped`` with
a reason and surface in the review summary.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from newsletter_engine.ingestion import chunker
from newsletter_engine.ingestion.parsers import document, pptx, text, transcript_docx
from newsletter_engine.store.db import Database

SUPPORTED_EXTENSIONS = {".docx", ".pptx", ".pdf", ".txt", ".md"}


@dataclass
class IngestedSource:
    source_id: str
    path: Path
    folder: str
    input_type: str
    chunks: list[dict]


@dataclass
class SkippedFile:
    path: Path
    reason: str


@dataclass
class IngestResult:
    sources: list[IngestedSource] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)

    @property
    def all_chunks(self) -> list[dict]:
        return [chunk for source in self.sources for chunk in source.chunks]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _detect_and_parse(path: Path) -> tuple[str, list[chunker.ParsedChunk]]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        # Transcript-vs-document sniffing (FR-002a)
        if transcript_docx.looks_like_transcript(path):
            return "transcript", transcript_docx.parse(path)
        return "document", document.parse_docx(path)
    if suffix == ".pptx":
        return "pptx", pptx.parse(path)
    if suffix == ".pdf":
        return "document", document.parse_pdf(path)
    if suffix in (".txt", ".md"):
        return "text", text.parse(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def ingest(
    source_dir: str | Path,
    *,
    edition_id: str,
    db: Database,
    classification_default: str,
    log=None,
) -> IngestResult:
    """Scan ``source_dir`` recursively, parse every supported file, persist provenance."""
    source_dir = Path(source_dir)
    result = IngestResult()

    if not source_dir.is_dir():
        if log:
            log.warning("source_dir_missing", source_dir=str(source_dir))
        return result

    for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        if path.name.startswith("~$"):  # Office lock files
            continue
        folder = str(path.parent.relative_to(source_dir)) if path.parent != source_dir else "."

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            reason = f"unsupported file type '{path.suffix}'"
            db.insert_source_document(
                edition_id=edition_id,
                path=str(path),
                folder=folder,
                input_type="unknown",
                sha256="",
                classification=classification_default,
                status="skipped",
                skip_reason=reason,
            )
            result.skipped.append(SkippedFile(path=path, reason=reason))
            if log:
                log.info("file_skipped", path=str(path), reason=reason)
            continue

        try:
            sha256 = _sha256(path)
            if db.source_hash_exists(edition_id, sha256):
                raise ValueError("duplicate content (same hash already ingested)")
            input_type, parsed = _detect_and_parse(path)
            if not parsed:
                raise ValueError("no extractable content")
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}" if not isinstance(exc, ValueError) else str(exc)
            db.insert_source_document(
                edition_id=edition_id,
                path=str(path),
                folder=folder,
                input_type="unknown",
                sha256="",
                classification=classification_default,
                status="skipped",
                skip_reason=reason,
            )
            result.skipped.append(SkippedFile(path=path, reason=reason))
            if log:
                log.info("file_skipped", path=str(path), reason=reason)
            continue

        source_id = db.insert_source_document(
            edition_id=edition_id,
            path=str(path),
            folder=folder,
            input_type=input_type,
            sha256=sha256,
            classification=classification_default,
            status="ingested",
        )
        chunks = chunker.to_content_chunks(source_id, parsed)
        result.sources.append(
            IngestedSource(
                source_id=source_id,
                path=path,
                folder=folder,
                input_type=input_type,
                chunks=chunks,
            )
        )
        if log:
            log.info(
                "file_ingested",
                path=str(path),
                folder=folder,
                input_type=input_type,
                chunks=len(chunks),
            )

    return result
