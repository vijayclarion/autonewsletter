# Phase 0 Research: RAG Engine Architecture & Pipeline Flow Document

**Date**: 2026-06-15
**Plan**: [plan.md](plan.md)

The Technical Context had no `NEEDS CLARIFICATION` markers — the spec's Assumptions already
resolved format and location. The decisions below record those choices and the few authoring
conventions worth fixing before drafting.

## R1 — Source of truth for the description

- **Decision**: Treat the `001-may-newsletter-pipeline` artifacts as authoritative:
  `spec.md` (FR/SC and entities), `plan.md` (technical context + project structure),
  `data-model.md` (entities, fields, state machine), and `contracts/` (CLI + config). Read
  the actual `src/newsletter_engine/` tree to confirm module names when mapping stages to code.
- **Rationale**: The request is to describe the *existing* engine. The `001` artifacts are the
  agreed design of record; deriving the document from them keeps it accurate and avoids
  re-inventing behavior. Spec Assumptions already declare these the source of truth on divergence.
- **Alternatives considered**: Reverse-engineer solely from code (rejected — slower, and code
  may be partially implemented; artifacts capture intended design). Interview-only (rejected —
  no need; artifacts are complete).

## R2 — Document format and diagram tooling

- **Decision**: GitHub-flavored Markdown for the document; the end-to-end flow diagram authored
  in **Mermaid** fenced code blocks. Per-stage detail presented as a consistent
  "Inputs / Outputs / Consumed by / On failure / Code location" block, plus a summary table.
- **Rationale**: Markdown is renderable everywhere in the repo with zero tooling; Mermaid is
  already the engine's diagram-as-code convention (constitution Principle IV), so the document
  practices what it documents and the diagram stays diffable/regenerable. A uniform per-stage
  block makes FR-007 (inputs/outputs/consumer for every stage) mechanically checkable.
- **Alternatives considered**: PDF/Word (rejected — not diffable, not source-controlled well).
  PlantUML (rejected — Mermaid is the project default and sufficient here). Prose-only flow with
  no diagram (rejected — FR-005 requires an end-to-end diagram).

## R3 — Location of the deliverable

- **Decision**: `docs/rag-engine-architecture.md` at the repository root.
- **Rationale**: The audience includes engineers and the producer; a top-level `docs/` folder is
  the conventional, discoverable home for an internal reference, separate from the per-feature
  `specs/` planning trail. Keeps the "what the engine is" reference distinct from "how we planned
  feature 002."
- **Alternatives considered**: Inside `specs/002-rag-pipeline-architecture/` (rejected — buries
  a living reference under a feature-planning directory). Repo README (rejected — too long; the
  README should link to it instead).

## R4 — Stage decomposition to document

- **Decision**: Document the pipeline as this ordered stage list, matching the `001` structure:
  1. **Scan & Ingest** (`ingestion/scanner.py`, `ingestion/parsers/`, `ingestion/chunker.py`)
  2. **Classify** technical vs non-technical (`classification/`)
  3. **Redact** PII / speaker→role (`redaction/`)
  4. **Chunk → Embed → Store** locally (`retrieval/` + ChromaDB; embeddings local)
  5. **Retrieve** eligible chunks (`retrieval/`)
  6. **Generate** stories, diagrams, citations, TL;DR, action items (`generation/`, `models/`,
     `prompts/`)
  7. **Render** web + print (`rendering/`)
  8. **Report** the informational run report (`report/`, `observability/`)
  9. **Archive** immutable hashed edition (`archive/`, `store/`)
- **Rationale**: This mirrors the `001` plan's source layout and data-model flow
  (SourceDocument → ContentChunk → retrieval → Section/Diagram/Citation → Edition → RunReport
  → archive), so every stage maps cleanly to a real directory (FR-013) and the data handoffs
  (FR-006) follow the entity relationships.
- **Alternatives considered**: Collapsing classify+redact or embed+retrieve into single stages
  (rejected — separate code modules and distinct inputs/outputs warrant separate entries for
  FR-007). Finer-grained substeps (deferred — the per-stage block can note substeps without
  exploding the top-level flow).

## R5 — Handling failure / empty-output paths (FR-011)

- **Decision**: Each per-stage block carries an explicit "On failure / empty output" line:
  ingest → skipped-files list with reason; classify → ambiguous content excluded and listed;
  diagram generation → drop after ≤2 retries and flag; section with thin support → omit/flag
  rather than fabricate; no action items found → section gap noted in edition + run report.
- **Rationale**: FR-011 and the spec edge cases require documenting the non-happy paths; the
  `001` data-model already defines these (skip_reason, `ambiguous` label, diagram `failed`
  status, section `flags`), so the document reflects existing behavior, not new design.
- **Alternatives considered**: Happy-path only (rejected — fails FR-011).

## R6 — Secret / privacy hygiene in the document (FR-015)

- **Decision**: Reference provider configuration by environment-variable **name** only; use
  synthetic, illustrative examples for any chunk/citation samples; include no real transcript
  text and no key values. A final no-secrets pass satisfies SC-005.
- **Rationale**: Constitution privacy constraints forbid secrets/raw content in repo artifacts;
  the document is a committed artifact and must comply.
- **Alternatives considered**: Quoting real `Documents/` content as examples (rejected — privacy
  violation). Showing a sample `.env` with placeholder-but-realistic keys (rejected — use
  variable names only, never key-shaped strings).

**All decisions resolved — no open `NEEDS CLARIFICATION`.**
