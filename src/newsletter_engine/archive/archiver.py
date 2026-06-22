"""Immutable edition archive with hashed manifest (FR-023, constitution Principle IX).

Invoked automatically at the end of a successful ``run`` (amendment 2026-06-11: no
approval step exists). Archives rendered outputs, diagram sources, the run report,
prompt/config versions, and run logs under ``archive/<month>/``, then writes
``manifest.json`` with a SHA-256 hash of every artifact and transitions the edition to
its terminal ``archived`` state.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from newsletter_engine.config import AppConfig
from newsletter_engine.store.db import Database


class ArchiveError(Exception):
    """Archiving cannot proceed (wrong state, missing outputs, target exists)."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def archive_edition(db: Database, cfg: AppConfig, month: str) -> dict:
    edition = db.get_edition(month)
    if edition is None:
        raise ArchiveError(f"Edition {month} does not exist")
    if edition["status"] != "final":
        raise ArchiveError(
            f"Edition {month} is '{edition['status']}'; only final editions can be archived"
        )

    edition_dir = cfg.output_dir / month
    if not edition_dir.is_dir():
        raise ArchiveError(f"No outputs found at {edition_dir}")
    dest = cfg.archive_dir / month
    if dest.exists():
        raise ArchiveError(f"Archive {dest} already exists; archives are immutable")

    dest.mkdir(parents=True)

    # Rendered outputs, diagram sources, run report
    for relative in ("edition", "report", "run-report.json"):
        source = edition_dir / relative
        if source.is_dir():
            shutil.copytree(source, dest / relative)
        elif source.is_file():
            shutil.copy2(source, dest / relative)

    # Prompt and config versions in force at archive time
    prompts_dest = dest / "prompts"
    prompts_dest.mkdir()
    for prompt_file in sorted((cfg.root_dir / "prompts").glob("*.md")):
        shutil.copy2(prompt_file, prompts_dest / prompt_file.name)
    config_dest = dest / "config"
    config_dest.mkdir()
    for config_file in sorted(cfg.config_dir.glob("*.yaml")):
        shutil.copy2(config_file, config_dest / config_file.name)

    # Run logs for the edition's pipeline runs
    runs_dest = dest / "runs"
    runs_dest.mkdir()
    for run in db.runs_for_edition(month):
        log_path = Path(run["log_path"]) if run["log_path"] else None
        if log_path and log_path.exists():
            shutil.copy2(log_path, runs_dest / f"{run['id']}.jsonl")

    # Hash manifest covering every archived artifact (FR-023)
    artifacts = {}
    for path in sorted(p for p in dest.rglob("*") if p.is_file()):
        artifacts[path.relative_to(dest).as_posix()] = _sha256(path)
    manifest = {
        "edition": month,
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "template_version": edition["template_version"],
        "classification_label": edition["classification_label"],
        "algorithm": "sha256",
        "artifacts": artifacts,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    db.transition_edition(month, "archived")
    return {"archive_dir": str(dest), "artifacts": len(artifacts)}


def verify_manifest(archive_dir: Path) -> list[str]:
    """Re-hash archived artifacts against manifest.json; returns mismatch descriptions."""
    manifest = json.loads((archive_dir / "manifest.json").read_text(encoding="utf-8"))
    problems = []
    for relative, expected in manifest["artifacts"].items():
        path = archive_dir / relative
        if not path.exists():
            problems.append(f"missing: {relative}")
        elif _sha256(path) != expected:
            problems.append(f"hash mismatch: {relative}")
    return problems
