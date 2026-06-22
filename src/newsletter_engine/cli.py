"""``newsletter`` CLI (contracts/cli-interface.md).

Exit codes: 0 success, 1 operational failure, 2 usage error (Typer's default).
"""

from __future__ import annotations

import datetime as _dt
import json as _json
import os
import re
import sys
from pathlib import Path

import typer

from newsletter_engine.archive.archiver import ArchiveError, archive_edition
from newsletter_engine.classification import classifier
from newsletter_engine.config import ConfigError, load_config, load_key_fallbacks
from newsletter_engine.generation import diagrams as diagram_gen
from newsletter_engine.generation import writer as writer_mod
from newsletter_engine.ingestion import scanner
from newsletter_engine.models.provider import ModelCallError
from newsletter_engine.models.router import ModelRouter
from newsletter_engine.observability.cost import CostTracker
from newsletter_engine.observability.logging import setup_run_logging
from newsletter_engine.observability.report import StageTimer, write_report
from newsletter_engine.redaction import redactor
from newsletter_engine.rendering import pdf as pdf_render
from newsletter_engine.rendering import render
from newsletter_engine.rendering.render import TEMPLATE_VERSION
from newsletter_engine.report import classification as classification_mod
from newsletter_engine.report import summary as run_report
from newsletter_engine.report.trace import TraceError, trace_citation
from newsletter_engine.retrieval.index import ChunkIndex
from newsletter_engine.store.db import Database, InvalidTransition, new_id

app = typer.Typer(name="newsletter", help="RAG newsletter pipeline: run, trace, archive.")
PROMPT_FILES = {
    "classifier": "classifier.v1",
    "writer_story": "writer-story.v1",
    "writer_tldr": "writer-tldr.v1",
    "diagrammer": "diagrammer.v1",
    "alt_text": "alt-text.v1",
}
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@app.callback()
def _main() -> None:
    """Generate and archive monthly technical newsletters (final upon generation)."""


def _load_dotenv(root_dir: Path) -> None:
    env_file = root_dir / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _load_prompts(root_dir: Path) -> dict[str, str]:
    prompts = {}
    for key, version in PROMPT_FILES.items():
        path = root_dir / "prompts" / f"{version}.md"
        if not path.exists():
            raise ConfigError(f"Missing prompt artifact: {path}")
        prompts[key] = path.read_text(encoding="utf-8")
    return prompts


def _fail(message: str) -> None:
    typer.echo(f"ERROR: {message}", err=True)
    raise typer.Exit(code=1)


@app.command()
def run(
    month: str = typer.Option(..., "--month", help="Edition month, ISO YYYY-MM"),
    source: Path | None = typer.Option(None, "--source", help="Source folder (default: config)"),
    config: Path = typer.Option(Path("config/config.yaml"), "--config"),
    json_output: bool = typer.Option(False, "--json", help="Final summary as JSON"),
) -> None:
    """Execute the full pipeline for an edition (ingest -> ... -> render)."""
    if not _MONTH_RE.match(month):
        typer.echo(f"ERROR: --month must be ISO YYYY-MM, got '{month}'", err=True)
        raise typer.Exit(code=2)

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        _fail(str(exc))

    _load_dotenv(cfg.root_dir)
    load_key_fallbacks(cfg.root_dir)
    source_dir = source if source is not None else cfg.source_dir

    run_id = new_id()
    run_dir = cfg.root_dir / "runs" / run_id
    log, log_path = setup_run_logging(run_dir)
    cost = CostTracker(pricing=cfg.models.pricing)
    router = ModelRouter(cfg.models, log=log, cost_tracker=cost)
    db = Database(cfg.root_dir / "newsletter.db")
    timer = StageTimer(log=log)
    started_at = _dt.datetime.now(_dt.timezone.utc).isoformat()

    try:
        prompts = _load_prompts(cfg.root_dir)
    except ConfigError as exc:
        _fail(str(exc))

    edition = db.get_or_create_edition(
        month, classification_label=cfg.classification_default,
        template_version=TEMPLATE_VERSION,
    )
    if edition["status"] == "final":
        db.transition_edition(month, "generating")  # re-run replaces the edition
    elif edition["status"] != "generating":
        _fail(f"Edition {month} is '{edition['status']}' and cannot be re-run")
    db.set_edition_template_version(month, TEMPLATE_VERSION)

    db.start_run(month, str(log_path), list(PROMPT_FILES.values()), run_id=run_id)
    db.replace_edition_content(month)
    log.info("run_started", run_id=run_id, month=month, source_dir=str(source_dir))
    typer.echo(f"Run {run_id} — edition {month}")

    edition_dir = cfg.output_dir / month
    outcome = "edition_ready"

    try:
        # ---- ingest (FR-001..004) ----
        with timer.stage("ingest"):
            ingest_result = scanner.ingest(
                source_dir,
                edition_id=month,
                db=db,
                classification_default=cfg.classification_default,
                log=log,
            )
        chunks = ingest_result.all_chunks
        typer.echo(
            f"Ingested {len(ingest_result.sources)} file(s), "
            f"{len(ingest_result.skipped)} skipped, {len(chunks)} chunk(s)"
        )

        # ---- classify (FR-006..008) ----
        with timer.stage("classify"):
            outcome_cls = classifier.classify_chunks(
                chunks,
                router=router,
                prompt_text=prompts["classifier"],
                confidence_threshold=cfg.classifier.confidence_threshold,
                log=log,
            )
        typer.echo(
            f"Classified: {outcome_cls.technical} technical, "
            f"{outcome_cls.non_technical} non-technical, {outcome_cls.ambiguous} ambiguous"
        )

        # ---- redact (FR-009/FR-019), then persist (only redacted text is stored) ----
        with timer.stage("redact"):
            redactor.redact_chunks(chunks, cfg.redaction, log=log)
            db.insert_chunks(chunks)

        chunk_lookup = {c["id"]: c for c in chunks}
        eligible = [c for c in chunks if c["eligible"]]

        sections_out: list[dict] = []
        stories: list[writer_mod.StoryDraft] = []
        omitted_sections: list[dict] = []
        failed_diagrams: list[dict] = []
        run_notes: list[str] = []
        diagrams_valid = 0

        if not eligible:
            outcome = "nothing_to_publish"
            typer.echo("No eligible technical content — nothing to publish.")
        else:
            # ---- index (technical-only retrieval) ----
            with timer.stage("index"):
                index = ChunkIndex(cfg.root_dir / ".chroma", router, log=log)
                index.reset_edition(month)
                indexed = index.add_chunks(month, chunks)
            typer.echo(f"Indexed {indexed} eligible chunk(s)")

            # ---- generate (FR-010/011/014) ----
            with timer.stage("generate"):
                topics = writer_mod.group_topics(chunks, router=router, log=log)
                for topic in topics:
                    draft = writer_mod.write_story(
                        topic,
                        edition_id=month,
                        chunk_lookup=chunk_lookup,
                        index=index,
                        router=router,
                        prompt_text=prompts["writer_story"],
                        log=log,
                    )
                    if draft.insufficient_support:
                        omitted_sections.append(
                            {"topic": topic.title,
                             "reason": "insufficient supporting content (FR-014)"}
                        )
                        log.info("section_omitted", topic=topic.title)
                    else:
                        stories.append(draft)

                tldr_md = (
                    writer_mod.write_tldr(
                        stories, router=router, prompt_text=prompts["writer_tldr"], log=log
                    )
                    if stories
                    else ""
                )
                action_items_md = writer_mod.write_action_items(chunks, router=router, log=log)

            if not stories:
                outcome = "nothing_to_publish"
                typer.echo("No story survived citation validation — nothing to publish.")

        if outcome == "edition_ready":
            # ---- diagrams (FR-012/013/018) ----
            diagrams_dir = edition_dir / "edition" / "diagrams"
            story_diagrams: dict[int, diagram_gen.DiagramResult] = {}
            with timer.stage("diagrams"):
                for i, story in enumerate(stories):
                    result = diagram_gen.generate_for_section(
                        section_title=story.title,
                        body_md=story.body_md,
                        router=router,
                        diagrammer_prompt=prompts["diagrammer"],
                        alt_text_prompt=prompts["alt_text"],
                        max_retries=cfg.diagrams.max_regeneration_retries,
                        diagrams_dir=diagrams_dir,
                        log=log,
                    )
                    if result is None:
                        continue
                    if result.status == "valid":
                        story_diagrams[i] = result
                        diagrams_valid += 1
                    else:
                        story.flags.append("diagram_dropped")
                        failed_diagrams.append(
                            {"section_title": story.title, "reason": result.failure_reason}
                        )
            typer.echo(
                f"Stories: {len(stories)}; diagrams: {diagrams_valid} valid, "
                f"{len(failed_diagrams)} dropped"
            )

            # ---- persist sections, citations, diagrams; build render model ----
            with timer.stage("render"):
                ordinal = 0
                references_md_parts: list[str] = []

                if tldr_md:
                    db.insert_section(
                        edition_id=month, kind="tldr", ordinal=ordinal,
                        title="TL;DR", body_md=tldr_md,
                    )
                    sections_out.append(
                        {"kind": "tldr", "title": "TL;DR", "body_md": tldr_md, "diagrams": []}
                    )
                    ordinal += 1

                for i, story in enumerate(stories):
                    section_id = db.insert_section(
                        edition_id=month, kind="story", ordinal=ordinal,
                        title=story.title, body_md=story.body_md, flags=story.flags,
                    )
                    ref_lines = [f"**{story.title}**", ""]
                    for citation in story.citations:
                        citation_id = db.insert_citation(
                            section_id=section_id,
                            statement_anchor=citation.anchor,
                            chunk_ids=citation.chunk_ids,
                        )
                        chunk = chunk_lookup[citation.chunk_ids[0]]
                        src = db.get_source(chunk["source_id"])
                        location = _json.dumps(chunk["location"])
                        ref_lines.append(
                            f"- [{citation.anchor}] `{citation_id}` — "
                            f"{Path(src['path']).name} {location}"
                        )
                    references_md_parts.append("\n".join(ref_lines))

                    section_diagrams = []
                    diagram = story_diagrams.get(i)
                    if diagram is not None:
                        db.insert_diagram(
                            section_id=section_id,
                            mermaid_src=diagram.mermaid_src,
                            caption=diagram.caption,
                            alt_text=diagram.alt_text,
                            status="valid",
                            svg_path=str(diagram.svg_path),
                        )
                        section_diagrams.append(
                            {
                                "svg_path": diagram.svg_path,
                                "caption": diagram.caption,
                                "alt_text": diagram.alt_text,
                            }
                        )
                    for failed in (f for f in failed_diagrams
                                   if f["section_title"] == story.title):
                        db.insert_diagram(
                            section_id=section_id,
                            mermaid_src="", caption="", alt_text="",
                            status="failed", svg_path=None,
                        )
                    sections_out.append(
                        {"kind": "story", "title": story.title, "body_md": story.body_md,
                         "diagrams": section_diagrams}
                    )
                    ordinal += 1

                if action_items_md:
                    db.insert_section(
                        edition_id=month, kind="action_items", ordinal=ordinal,
                        title="Action Items", body_md=action_items_md,
                    )
                    sections_out.append(
                        {"kind": "action_items", "title": "Action Items",
                         "body_md": action_items_md, "diagrams": []}
                    )
                    ordinal += 1

                references_md = "\n\n".join(references_md_parts) or "No citations recorded."
                db.insert_section(
                    edition_id=month, kind="references", ordinal=ordinal,
                    title="References", body_md=references_md,
                )
                sections_out.append(
                    {"kind": "references", "title": "References",
                     "body_md": references_md, "diagrams": []}
                )

                # Edition label = max-restrictive over its sources (FR-017)
                edition_label = classification_mod.derive_label(
                    [s["classification"] for s in db.sources_for_edition(month)
                     if s["status"] == "ingested"],
                    default=cfg.classification_default,
                )
                db.set_edition_classification(month, edition_label)

                edition_path = render.render_edition(
                    brand=cfg.brand,
                    month=month,
                    edition_number=edition["number"],
                    classification_label=edition_label,
                    sections=sections_out,
                    out_path=edition_dir / "edition" / "newsletter.html",
                )
            typer.echo(f"Edition rendered: {edition_path}")

            # ---- print-style PDF (FR-026) ----
            with timer.stage("pdf") as pdf_stage:
                try:
                    pdf_path = pdf_render.render_pdf(
                        edition_path, edition_dir / "edition" / "newsletter.pdf"
                    )
                    typer.echo(f"PDF rendered: {pdf_path}")
                except pdf_render.PdfRenderError as exc:
                    pdf_stage["error"] = str(exc)
                    run_notes.append(f"PDF rendering failed: {exc}")
                    log.warning("pdf_render_failed", error=str(exc))
                    typer.echo(f"WARNING: PDF rendering failed: {exc}", err=True)

        # ---- informational run report (FR-020) ----
        excluded_for_summary = []
        for chunk in chunks:
            if chunk["eligible"]:
                continue
            src = db.get_source(chunk["source_id"])
            reason = (
                "classified as non-technical"
                if chunk["label"] == "non_technical"
                else "ambiguous: below confidence threshold or unlabelled"
            )
            excluded_for_summary.append(
                {
                    "chunk_id": chunk["id"],
                    "source_path": Path(src["path"]).name,
                    "location": _json.dumps(chunk["location"]),
                    "label": chunk["label"],
                    "reason": reason,
                }
            )
        summary_path = run_report.write_summary(
            month=month,
            out_path=edition_dir / "report" / "summary.md",
            skipped_files=[{"path": str(s.path), "reason": s.reason}
                           for s in ingest_result.skipped],
            excluded_chunks=excluded_for_summary,
            omitted_sections=omitted_sections,
            flagged_sections=[{"title": s.title, "flags": s.flags}
                              for s in stories if s.flags],
            failed_diagrams=failed_diagrams,
            pending_brand_assets=cfg.brand.pending_brand_assets,
            notes=run_notes,
        )
        report_flags = [{"title": s.title, "flags": s.flags} for s in stories if s.flags]
        db.upsert_run_report(month, str(summary_path), report_flags)
        typer.echo(f"Run report: {summary_path}")

        # ---- run report (FR-024) ----
        finished_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
        chunk_counts = {
            "total": len(chunks),
            "technical": sum(1 for c in chunks if c["label"] == "technical"),
            "non_technical": sum(1 for c in chunks if c["label"] == "non_technical"),
            "ambiguous": sum(1 for c in chunks if c["label"] == "ambiguous"),
            "eligible": len(eligible),
        }
        report_path = write_report(
            out_path=edition_dir / "run-report.json",
            run_id=run_id,
            month=month,
            started_at=started_at,
            finished_at=finished_at,
            stages=timer.stages,
            files={
                "ingested": len(ingest_result.sources),
                "skipped": len(ingest_result.skipped),
            },
            chunks=chunk_counts,
            sections={
                "stories": len(stories),
                "omitted": len(omitted_sections),
                "total_rendered": len(sections_out),
            },
            diagrams={"valid": diagrams_valid, "failed": len(failed_diagrams)},
            cost=cost.summary(),
            prompt_versions=list(PROMPT_FILES.values()),
            outcome=outcome,
        )
        db.finish_run(
            run_id,
            files_ingested=len(ingest_result.sources),
            files_skipped=len(ingest_result.skipped),
            stages=timer.stages,
            cost=cost.summary(),
        )

        log.info("run_finished", run_id=run_id, outcome=outcome)

        edition_status = edition["status"]
        if outcome == "edition_ready":
            # Final upon successful generation (FR-022), then archived automatically
            # (FR-023) — no review or approval step exists (amendment 2026-06-11).
            db.transition_edition(month, "final")
            edition_status = "final"
            try:
                archive_result = archive_edition(db, cfg, month)
                edition_status = "archived"
                typer.echo(
                    f"Archived to {archive_result['archive_dir']} "
                    f"({archive_result['artifacts']} artifacts hashed in manifest.json)."
                )
            except ArchiveError as exc:
                log.warning("auto_archive_failed", error=str(exc))
                typer.echo(
                    f"WARNING: automatic archiving failed ({exc}); the edition is final —"
                    f" run 'newsletter archive --month {month}' to retry.",
                    err=True,
                )

        summary = {
            "run_id": run_id,
            "month": month,
            "outcome": outcome,
            "status": edition_status,
            "files": {"ingested": len(ingest_result.sources),
                      "skipped": len(ingest_result.skipped)},
            "chunks": chunk_counts,
            "stories": len(stories),
            "diagrams": {"valid": diagrams_valid, "failed": len(failed_diagrams)},
            "cost_usd": cost.summary()["total_cost_usd"],
            "report": str(report_path),
        }
        if json_output:
            typer.echo(_json.dumps(summary, indent=2))
        else:
            typer.echo(
                f"Done ({outcome}). Cost: ${summary['cost_usd']}. Report: {report_path}"
            )

    except (ModelCallError, InvalidTransition, OSError) as exc:
        log.error("run_failed", run_id=run_id, error=str(exc))
        _fail(f"pipeline failed: {exc}")
    finally:
        db.close()


def _open(config: Path) -> tuple:
    """Shared command bootstrap: config + database."""
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        _fail(str(exc))
    return cfg, Database(cfg.root_dir / "newsletter.db")


@app.command()
def trace(
    month: str = typer.Option(..., "--month", help="Edition month, ISO YYYY-MM"),
    citation: str = typer.Option(..., "--citation", help="Citation id (see References)"),
    config: Path = typer.Option(Path("config/config.yaml"), "--config"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Resolve a citation to its source file, location, and supporting excerpt (FR-021)."""
    cfg, db = _open(config)
    try:
        result = trace_citation(db, month, citation)
    except TraceError as exc:
        _fail(str(exc))
    finally:
        db.close()

    if json_output:
        typer.echo(_json.dumps(result, indent=2))
        return
    typer.echo(f"Citation {result['citation_id']} (anchor [{result['anchor']}])")
    typer.echo(f"Section: {result['section']}")
    for support in result["supports"]:
        if "error" in support:
            typer.echo(f"  - chunk {support['chunk_id']}: {support['error']}")
            continue
        typer.echo(f"  - File: {support['file']} ({support['input_type']})")
        typer.echo(f"    Location: {_json.dumps(support['location'])}")
        typer.echo(f"    Excerpt: {support['excerpt']}")


@app.command()
def archive(
    month: str = typer.Option(..., "--month", help="Edition month, ISO YYYY-MM"),
    config: Path = typer.Option(Path("config/config.yaml"), "--config"),
) -> None:
    """Manually retry archiving a final edition (normally automatic after run, FR-023)."""
    cfg, db = _open(config)
    try:
        result = archive_edition(db, cfg, month)
    except ArchiveError as exc:
        _fail(str(exc))
    finally:
        db.close()

    typer.echo(
        f"Edition {month} archived to {result['archive_dir']} "
        f"({result['artifacts']} artifacts hashed in manifest.json)."
    )


@app.command()
def status(
    month: str = typer.Option(..., "--month", help="Edition month, ISO YYYY-MM"),
    config: Path = typer.Option(Path("config/config.yaml"), "--config"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show edition state (generating | final | archived), file counts, and flags."""
    cfg, db = _open(config)
    try:
        edition = db.get_edition(month)
        if edition is None:
            _fail(f"Edition {month} does not exist — run the pipeline first")
        sources = db.sources_for_edition(month)
        sections = db.sections_for_edition(month)
        record = db.get_run_report(month)
        flagged = [
            {"title": s["title"], "flags": _json.loads(s["flags"])}
            for s in sections
            if _json.loads(s["flags"])
        ]
        result = {
            "month": month,
            "status": edition["status"],
            "edition_number": edition["number"],
            "classification_label": edition["classification_label"],
            "template_version": edition["template_version"],
            "files": {
                "ingested": sum(1 for s in sources if s["status"] == "ingested"),
                "skipped": sum(1 for s in sources if s["status"] == "skipped"),
            },
            "sections": len(sections),
            "flags_outstanding": flagged,
            "run_report": record["report_path"] if record else None,
        }
    finally:
        db.close()

    if json_output:
        typer.echo(_json.dumps(result, indent=2))
        return
    typer.echo(f"Edition {month} — status: {result['status']}")
    typer.echo(
        f"  #{result['edition_number']}, classification {result['classification_label']}, "
        f"template {result['template_version']}"
    )
    typer.echo(
        f"  Files: {result['files']['ingested']} ingested, {result['files']['skipped']} skipped; "
        f"sections: {result['sections']}"
    )
    if result["flags_outstanding"]:
        for item in result["flags_outstanding"]:
            typer.echo(f"  Flag: {item['title']} — {', '.join(item['flags'])}")
    else:
        typer.echo("  No outstanding flags.")
    if result["run_report"]:
        typer.echo(f"  Run report: {result['run_report']}")


if __name__ == "__main__":
    sys.exit(app())
