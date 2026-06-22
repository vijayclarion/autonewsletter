"""Run report generation (FR-024, constitution Principle VI).

A machine-readable JSON summary per pipeline run: stage timings, counts, cost, and the
prompt versions used — everything needed to account for a run without reading the logs.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path


class StageTimer:
    """Collects per-stage wall-clock timings and statuses."""

    def __init__(self, log=None):
        self.stages: dict[str, dict] = {}
        self._log = log

    @contextmanager
    def stage(self, name: str, **counts):
        start = time.monotonic()
        if self._log:
            self._log.info("stage_started", stage=name)
        entry = {"status": "running"}
        self.stages[name] = entry
        try:
            yield entry
        except Exception:
            entry["status"] = "failed"
            raise
        else:
            entry["status"] = "completed"
        finally:
            entry["seconds"] = round(time.monotonic() - start, 3)
            if self._log:
                self._log.info(
                    "stage_finished", stage=name, status=entry["status"], seconds=entry["seconds"]
                )


def write_report(
    *,
    out_path: Path,
    run_id: str,
    month: str,
    started_at: str,
    finished_at: str,
    stages: dict,
    files: dict,
    chunks: dict,
    sections: dict,
    diagrams: dict,
    cost: dict,
    prompt_versions: list[str],
    outcome: str,
) -> Path:
    report = {
        "run_id": run_id,
        "month": month,
        "outcome": outcome,
        "started_at": started_at,
        "finished_at": finished_at,
        "stages": stages,
        "files": files,
        "chunks": chunks,
        "sections": sections,
        "diagrams": diagrams,
        "cost": cost,
        "prompt_versions": prompt_versions,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out_path
