# Data Model: May Technical Newsletter — Full Pipeline & Enterprise Template

**Date**: 2026-06-10 (amended 2026-06-11: review/approval removed)
**Plan**: [plan.md](plan.md)

Storage: SQLite (metadata/relationships) + ChromaDB (chunk embeddings, keyed by `chunk_id`)
+ filesystem (rendered outputs, diagram sources, archive). See research.md R4/R10.

## Entities

### SourceDocument

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT (uuid) | PK |
| edition_id | TEXT | FK → Edition |
| path | TEXT | original file path |
| folder | TEXT | containing folder added by producer (provenance, FR-001) |
| input_type | TEXT | `transcript` \| `pptx` \| `document` \| `text` (detected, FR-002a) |
| sha256 | TEXT | content hash (dedup + audit) |
| classification | TEXT | `internal` \| `confidential` \| `public` (default `internal`) |
| status | TEXT | `ingested` \| `skipped` |
| skip_reason | TEXT NULL | required when `skipped` (FR-004) |
| ingested_at | TEXT (ISO) | |

### ContentChunk

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT (uuid) | PK; same id keys the ChromaDB embedding |
| source_id | TEXT | FK → SourceDocument |
| ordinal | INTEGER | order within source |
| text | TEXT | redacted text (post FR-009; raw text never stored in logs) |
| location | JSON | `{page}` \| `{slide}` \| `{timestamp, speaker_role}` \| `{lines}` (FR-003) |
| label | TEXT | `technical` \| `non_technical` \| `ambiguous` (FR-006/FR-008) |
| label_confidence | REAL | classifier confidence |
| eligible | BOOLEAN | derived: `label == technical AND confidence >= threshold` |

### Edition

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT | e.g., `2026-05` |
| number | INTEGER | sequential edition number (masthead) |
| month | TEXT | ISO month |
| status | TEXT | see state machine below |
| classification_label | TEXT | max-restrictive over its SourceDocuments (FR-017) |
| template_version | TEXT | central template version used (FR-015/FR-016) |
| created_at / finalized_at | TEXT NULL | |

**State machine**: `generating → final → archived` *(amendment 2026-06-11: the former
`draft → in_review → approved → archived` review states are removed)*
- `generating → final`: pipeline run completed successfully, run report produced; the
  edition is final immediately — no approval state exists (FR-022)
- `final → archived`: archive manifest written + hashed automatically after generation
  (FR-023); terminal
- A re-run of a `final` (not yet archived) edition replaces it and returns to
  `generating`; an `archived` edition is immutable and a re-run is rejected

### Section

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT (uuid) | PK |
| edition_id | TEXT | FK → Edition |
| kind | TEXT | `tldr` \| `story` \| `action_items` \| `references` (order fixed by template) |
| ordinal | INTEGER | |
| title | TEXT | |
| body_md | TEXT | narrative markdown (context → exploration → outcome, FR-011) |
| flags | JSON | e.g., `insufficient_support`, `diagram_dropped`, `section_gap` (FR-014/FR-020) |

### Diagram

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT (uuid) | PK |
| section_id | TEXT | FK → Section (story) |
| mermaid_src | TEXT | declarative source (Principle IV) |
| caption | TEXT | required (FR-012) |
| alt_text | TEXT | required (FR-018) |
| status | TEXT | `valid` \| `failed` (after ≤2 regeneration retries, FR-013) |
| svg_path | TEXT NULL | rendered asset when valid |

### Citation

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT (uuid) | PK |
| section_id | TEXT | FK → Section |
| statement_anchor | TEXT | stable anchor of the cited statement in body_md |
| chunk_ids | JSON | supporting ContentChunk ids (≥1, FR-010/FR-021) |

### RunReport *(replaces ReviewRecord — amendment 2026-06-11)*

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT (uuid) | PK |
| edition_id | TEXT | FK → Edition |
| report_path | TEXT | informational run report file (FR-020) |
| flags | JSON | excluded/ambiguous chunks, skipped files, insufficient-support sections, failed diagrams — each with reason; informational only, gates nothing |

### PipelineRun

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT (uuid) | PK |
| edition_id | TEXT | FK → Edition |
| started_at / finished_at | TEXT | |
| files_ingested / files_skipped | INTEGER | |
| stages | JSON | per-stage timing/status |
| cost | JSON | per-model token counts + computed cost (FR-024, Principle VI) |
| log_path | TEXT | `runs/<run-id>/run.jsonl` |
| prompt_versions | JSON | versioned prompt ids used (Principle III) |

## Relationships

```
Edition 1—* SourceDocument 1—* ContentChunk
Edition 1—* Section 1—* Citation *—* ContentChunk (via chunk_ids)
Section (story) 1—* Diagram
Edition 1—* PipelineRun, Edition 1—1 RunReport
```

## Validation Rules (from spec)

- A `skipped` SourceDocument MUST have `skip_reason` (FR-004).
- Only `eligible = true` chunks may be retrieved for generation (FR-006–FR-008).
- Every Section statement anchor MUST have ≥1 Citation chunk id that resolves (FR-010, SC-002).
- A story Section describing architecture/flow/decision MUST reference ≥1 `valid` Diagram or
  carry the `diagram_dropped` flag (FR-012/FR-013).
- Edition `classification_label` = most restrictive of its sources' classifications (FR-017).
- Edition becomes `final` upon successful generation with no approval precondition; it is
  archived automatically afterward (FR-022/FR-023, amendment 2026-06-11).
- Archive manifest hashes MUST cover every archived artifact (FR-023).
