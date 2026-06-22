"""Per-run JSON-lines logging (constitution Principle VI).

One ``run.jsonl`` per pipeline run. Privacy rule: chunk *ids* only — raw chunk text must
never be passed to the logger.
"""

from __future__ import annotations

from pathlib import Path

import structlog


def setup_run_logging(run_dir: str | Path):
    """Configure structlog to append JSON lines to ``<run_dir>/run.jsonl``.

    Returns ``(logger, log_path)``.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "run.jsonl"
    log_file = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — lives for the run

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.WriteLoggerFactory(file=log_file),
        cache_logger_on_first_use=False,
    )
    return structlog.get_logger(), log_path
