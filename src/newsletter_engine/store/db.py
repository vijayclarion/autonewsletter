"""SQLite persistence for all data-model.md entities.

Edition state transitions are guarded here: anything outside the documented state machine
raises ``InvalidTransition``.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Edition state machine (data-model.md, amended 2026-06-11):
# generating -> final -> archived, with final -> generating on a re-run.
# No review/approval states exist; archived is terminal.
ALLOWED_TRANSITIONS: set[tuple[str, str]] = {
    ("generating", "final"),
    ("final", "archived"),
    ("final", "generating"),
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS editions (
    id TEXT PRIMARY KEY,
    number INTEGER NOT NULL,
    month TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generating',
    classification_label TEXT NOT NULL,
    template_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    finalized_at TEXT
);
CREATE TABLE IF NOT EXISTS source_documents (
    id TEXT PRIMARY KEY,
    edition_id TEXT NOT NULL REFERENCES editions(id),
    path TEXT NOT NULL,
    folder TEXT NOT NULL,
    input_type TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT 'internal',
    status TEXT NOT NULL,
    skip_reason TEXT,
    ingested_at TEXT NOT NULL,
    CHECK (status != 'skipped' OR skip_reason IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS content_chunks (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source_documents(id),
    ordinal INTEGER NOT NULL,
    text TEXT NOT NULL,
    location TEXT NOT NULL,
    label TEXT,
    label_confidence REAL,
    eligible INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    edition_id TEXT NOT NULL REFERENCES editions(id),
    kind TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    title TEXT NOT NULL,
    body_md TEXT NOT NULL,
    flags TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS diagrams (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL REFERENCES sections(id),
    mermaid_src TEXT NOT NULL,
    caption TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    status TEXT NOT NULL,
    svg_path TEXT
);
CREATE TABLE IF NOT EXISTS citations (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL REFERENCES sections(id),
    statement_anchor TEXT NOT NULL,
    chunk_ids TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run_reports (
    id TEXT PRIMARY KEY,
    edition_id TEXT NOT NULL UNIQUE REFERENCES editions(id),
    report_path TEXT NOT NULL,
    flags TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id TEXT PRIMARY KEY,
    edition_id TEXT NOT NULL REFERENCES editions(id),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    files_ingested INTEGER NOT NULL DEFAULT 0,
    files_skipped INTEGER NOT NULL DEFAULT 0,
    stages TEXT NOT NULL DEFAULT '{}',
    cost TEXT NOT NULL DEFAULT '{}',
    log_path TEXT,
    prompt_versions TEXT NOT NULL DEFAULT '[]'
);
"""


class InvalidTransition(Exception):
    """Raised on an edition state change outside the documented state machine."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


class Database:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- editions ---------------------------------------------------------

    def get_or_create_edition(
        self, month: str, *, classification_label: str, template_version: str
    ) -> sqlite3.Row:
        row = self.get_edition(month)
        if row is not None:
            return row
        number = 1 + (
            self._conn.execute("SELECT COUNT(*) AS n FROM editions").fetchone()["n"]
        )
        self._conn.execute(
            "INSERT INTO editions (id, number, month, status, classification_label,"
            " template_version, created_at) VALUES (?, ?, ?, 'generating', ?, ?, ?)",
            (month, number, month, classification_label, template_version, _now()),
        )
        self._conn.commit()
        return self.get_edition(month)

    def get_edition(self, edition_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM editions WHERE id = ?", (edition_id,)
        ).fetchone()

    def transition_edition(self, edition_id: str, new_status: str) -> None:
        row = self.get_edition(edition_id)
        if row is None:
            raise InvalidTransition(f"Edition '{edition_id}' does not exist")
        current = row["status"]
        if (current, new_status) not in ALLOWED_TRANSITIONS:
            raise InvalidTransition(
                f"Edition '{edition_id}': transition {current} -> {new_status} is not allowed"
            )
        finalized = _now() if new_status == "archived" else row["finalized_at"]
        self._conn.execute(
            "UPDATE editions SET status = ?, finalized_at = ? WHERE id = ?",
            (new_status, finalized, edition_id),
        )
        self._conn.commit()

    def set_edition_template_version(self, edition_id: str, version: str) -> None:
        self._conn.execute(
            "UPDATE editions SET template_version = ? WHERE id = ?", (version, edition_id)
        )
        self._conn.commit()

    def set_edition_classification(self, edition_id: str, label: str) -> None:
        self._conn.execute(
            "UPDATE editions SET classification_label = ? WHERE id = ?", (label, edition_id)
        )
        self._conn.commit()

    # -- sources & chunks --------------------------------------------------

    def replace_edition_content(self, edition_id: str) -> None:
        """Clear a previous run's rows so a re-run starts clean (idempotent runs)."""
        self._conn.execute(
            "DELETE FROM citations WHERE section_id IN"
            " (SELECT id FROM sections WHERE edition_id = ?)",
            (edition_id,),
        )
        self._conn.execute(
            "DELETE FROM diagrams WHERE section_id IN"
            " (SELECT id FROM sections WHERE edition_id = ?)",
            (edition_id,),
        )
        self._conn.execute("DELETE FROM sections WHERE edition_id = ?", (edition_id,))
        self._conn.execute(
            "DELETE FROM content_chunks WHERE source_id IN"
            " (SELECT id FROM source_documents WHERE edition_id = ?)",
            (edition_id,),
        )
        self._conn.execute("DELETE FROM source_documents WHERE edition_id = ?", (edition_id,))
        self._conn.commit()

    def insert_source_document(
        self,
        *,
        edition_id: str,
        path: str,
        folder: str,
        input_type: str,
        sha256: str,
        classification: str,
        status: str,
        skip_reason: str | None = None,
    ) -> str:
        if status == "skipped" and not skip_reason:
            raise ValueError("A skipped source document requires a skip_reason (FR-004)")
        doc_id = new_id()
        self._conn.execute(
            "INSERT INTO source_documents (id, edition_id, path, folder, input_type, sha256,"
            " classification, status, skip_reason, ingested_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                doc_id,
                edition_id,
                path,
                folder,
                input_type,
                sha256,
                classification,
                status,
                skip_reason,
                _now(),
            ),
        )
        self._conn.commit()
        return doc_id

    def insert_chunks(self, chunks: list[dict]) -> None:
        self._conn.executemany(
            "INSERT INTO content_chunks (id, source_id, ordinal, text, location, label,"
            " label_confidence, eligible) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    c["id"],
                    c["source_id"],
                    c["ordinal"],
                    c["text"],
                    json.dumps(c["location"]),
                    c.get("label"),
                    c.get("label_confidence"),
                    1 if c.get("eligible") else 0,
                )
                for c in chunks
            ],
        )
        self._conn.commit()

    def update_chunk_labels(self, chunks: list[dict]) -> None:
        self._conn.executemany(
            "UPDATE content_chunks SET text = ?, location = ?, label = ?,"
            " label_confidence = ?, eligible = ? WHERE id = ?",
            [
                (
                    c["text"],
                    json.dumps(c["location"]),
                    c.get("label"),
                    c.get("label_confidence"),
                    1 if c.get("eligible") else 0,
                    c["id"],
                )
                for c in chunks
            ],
        )
        self._conn.commit()

    def get_chunk(self, chunk_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM content_chunks WHERE id = ?", (chunk_id,)
        ).fetchone()

    def get_source(self, source_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM source_documents WHERE id = ?", (source_id,)
        ).fetchone()

    def sources_for_edition(self, edition_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM source_documents WHERE edition_id = ? ORDER BY path", (edition_id,)
        ).fetchall()

    def source_hash_exists(self, edition_id: str, sha256: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM source_documents WHERE edition_id = ? AND sha256 = ?"
            " AND status = 'ingested'",
            (edition_id, sha256),
        ).fetchone()
        return row is not None

    # -- sections / diagrams / citations -----------------------------------

    def insert_section(
        self,
        *,
        edition_id: str,
        kind: str,
        ordinal: int,
        title: str,
        body_md: str,
        flags: list[str] | None = None,
    ) -> str:
        section_id = new_id()
        self._conn.execute(
            "INSERT INTO sections (id, edition_id, kind, ordinal, title, body_md, flags)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (section_id, edition_id, kind, ordinal, title, body_md, json.dumps(flags or [])),
        )
        self._conn.commit()
        return section_id

    def insert_diagram(
        self,
        *,
        section_id: str,
        mermaid_src: str,
        caption: str,
        alt_text: str,
        status: str,
        svg_path: str | None,
    ) -> str:
        diagram_id = new_id()
        self._conn.execute(
            "INSERT INTO diagrams (id, section_id, mermaid_src, caption, alt_text, status,"
            " svg_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (diagram_id, section_id, mermaid_src, caption, alt_text, status, svg_path),
        )
        self._conn.commit()
        return diagram_id

    def insert_citation(
        self, *, section_id: str, statement_anchor: str, chunk_ids: list[str]
    ) -> str:
        citation_id = new_id()
        self._conn.execute(
            "INSERT INTO citations (id, section_id, statement_anchor, chunk_ids)"
            " VALUES (?, ?, ?, ?)",
            (citation_id, section_id, statement_anchor, json.dumps(chunk_ids)),
        )
        self._conn.commit()
        return citation_id

    def get_citation(self, citation_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM citations WHERE id = ?", (citation_id,)
        ).fetchone()

    # -- run reports (informational; gates nothing) -------------------------

    def upsert_run_report(
        self, edition_id: str, report_path: str, flags: list[dict] | None = None
    ) -> None:
        existing = self._conn.execute(
            "SELECT id FROM run_reports WHERE edition_id = ?", (edition_id,)
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE run_reports SET report_path = ?, flags = ? WHERE edition_id = ?",
                (report_path, json.dumps(flags or []), edition_id),
            )
        else:
            self._conn.execute(
                "INSERT INTO run_reports (id, edition_id, report_path, flags)"
                " VALUES (?, ?, ?, ?)",
                (new_id(), edition_id, report_path, json.dumps(flags or [])),
            )
        self._conn.commit()

    def get_run_report(self, edition_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM run_reports WHERE edition_id = ?", (edition_id,)
        ).fetchone()

    # -- pipeline runs -----------------------------------------------------

    def start_run(
        self, edition_id: str, log_path: str, prompt_versions: list[str], run_id: str | None = None
    ) -> str:
        run_id = run_id or new_id()
        self._conn.execute(
            "INSERT INTO pipeline_runs (id, edition_id, started_at, log_path, prompt_versions)"
            " VALUES (?, ?, ?, ?, ?)",
            (run_id, edition_id, _now(), log_path, json.dumps(prompt_versions)),
        )
        self._conn.commit()
        return run_id

    def finish_run(
        self,
        run_id: str,
        *,
        files_ingested: int,
        files_skipped: int,
        stages: dict,
        cost: dict,
    ) -> None:
        self._conn.execute(
            "UPDATE pipeline_runs SET finished_at = ?, files_ingested = ?, files_skipped = ?,"
            " stages = ?, cost = ? WHERE id = ?",
            (_now(), files_ingested, files_skipped, json.dumps(stages), json.dumps(cost), run_id),
        )
        self._conn.commit()

    def get_section(self, section_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM sections WHERE id = ?", (section_id,)
        ).fetchone()

    def runs_for_edition(self, edition_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM pipeline_runs WHERE edition_id = ? ORDER BY started_at",
            (edition_id,),
        ).fetchall()

    def sections_for_edition(self, edition_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM sections WHERE edition_id = ? ORDER BY ordinal", (edition_id,)
        ).fetchall()

    def diagrams_for_section(self, section_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM diagrams WHERE section_id = ?", (section_id,)
        ).fetchall()

    def citations_for_section(self, section_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM citations WHERE section_id = ?", (section_id,)
        ).fetchall()
