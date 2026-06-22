# Phase 1 Data Model: RAG Engine Architecture & Pipeline Flow Document

**Date**: 2026-06-15
**Plan**: [plan.md](plan.md)

This feature produces a document, not software, so there is no runtime storage. The "entities"
below are the structural building blocks of the **deliverable** — what the document is made of.
They drive the document outline ([contracts/document-outline.md](contracts/document-outline.md))
and let the Success Criteria be checked mechanically.

## Entities

### ArchitectureDocument

The single deliverable.

| Field | Type | Notes |
|-------|------|-------|
| title | text | "RAG Engine Architecture & Pipeline Flow" |
| describes_feature | text | `001-may-newsletter-pipeline` (subject under description) |
| engine_version_note | text | engine feature + date the description reflects (FR-003) |
| created_date | date | 2026-06-15 |
| overview | section | plain-language summary readable by a non-technical producer (FR-002, SC-006) |
| flow_diagram | FlowDiagram | end-to-end Mermaid diagram (FR-005, SC-004) |
| stages | StageDescription[] | ordered; one per pipeline stage (FR-004) |
| data_structures | DataStructureSummary[] | key structures moving through the pipeline (FR-009) |
| code_structure_map | CodeLocation[] | project layout + stage→code mapping (FR-012/FR-013) |
| final_outputs | text | rendered edition (web+print), run report, archived edition (FR-010) |

**Rules**: MUST contain no secrets/keys/real source content (FR-015, SC-005). MUST state the
engine version/feature + date (FR-003). MUST be understandable by both producer and engineer,
overview-first (FR-002).

### StageDescription

One per documented pipeline stage. The repeating heart of the document.

| Field | Type | Notes |
|-------|------|-------|
| ordinal | integer | position in the flow (1..N) |
| name | text | e.g., "Scan & Ingest", "Classify", "Retrieve" |
| purpose | text | what the stage does, one or two sentences |
| inputs | text[] | what it consumes (FR-007) |
| outputs | text[] | what it emits (FR-007) |
| consumed_by | text | next stage(s) that take the output (FR-006/FR-007) |
| failure_behavior | text | non-happy path output (FR-011): skip/exclude/drop/flag |
| code_location | CodeLocation | implementing directory/module (FR-013) |

**Rules**: every stage MUST populate `inputs`, `outputs`, and `consumed_by` (FR-007, SC-002).
For each adjacent pair, the earlier stage's `outputs` MUST describe the data the later stage's
`inputs` receives (FR-006). Stages with notable failure/empty behavior MUST populate
`failure_behavior` (FR-011).

### FlowDiagram

| Field | Type | Notes |
|-------|------|-------|
| format | text | Mermaid (diagram-as-code, Principle IV) |
| covers | text | every stage from source ingestion to archived edition (SC-004) |
| shows_data_flow | boolean | nodes are stages; edges labelled with the data passed (FR-005/FR-006) |

### DataStructureSummary

Conceptual description of a key structure that moves through the pipeline (FR-009). Sourced
from the `001` data-model.

| Field | Type | Notes |
|-------|------|-------|
| name | text | e.g., ContentChunk, Edition, Section, Diagram, Citation |
| purpose | text | what it represents in the flow |
| key_attributes | text[] | conceptual fields (e.g., chunk: text, provenance/location, label) |
| appears_between | text | which stages produce and consume it |

**Minimum set (FR-009)**: ContentChunk (with provenance + technical classification), plus
Edition, Section, Diagram, and Citation.

### CodeLocation

| Field | Type | Notes |
|-------|------|-------|
| path | text | directory or module, e.g., `src/newsletter_engine/retrieval/` |
| responsibility | text | what lives there |
| maps_to_stage | text NULL | the pipeline stage it implements (null for support dirs) |

**Rule**: every StageDescription MUST resolve to at least one CodeLocation (FR-013, SC-003);
support locations (`prompts/`, `config/`, `Documents/`, `editions/`, `archive/`) are described
with `maps_to_stage = null`.

## Relationships

```
ArchitectureDocument 1—1 FlowDiagram
ArchitectureDocument 1—* StageDescription 1—1 CodeLocation
ArchitectureDocument 1—* DataStructureSummary
ArchitectureDocument 1—* CodeLocation   (incl. support dirs not tied to a stage)
StageDescription.outputs ——(handoff, FR-006)——> next StageDescription.inputs
DataStructureSummary.appears_between ——> StageDescription pairs
```

## Validation Rules (from spec)

- Every StageDescription has non-empty `inputs`, `outputs`, `consumed_by` (FR-007, SC-002).
- The stage set is ordered and covers scan/ingest → classify → redact → chunk/embed/store →
  retrieve → generate → render → report → archive (FR-004).
- Exactly one end-to-end FlowDiagram covering all stages exists, in Mermaid (FR-005, SC-004).
- Every input type (text, PDF/Word, PPTX, transcript `.docx`) is enumerated, with the
  transcript-vs-document distinction explained, in the Ingest stage (FR-008).
- The minimum data-structure set is summarized (FR-009).
- Every stage maps to ≥1 CodeLocation (FR-013, SC-003).
- The document contains zero secrets/keys/real source content (FR-015, SC-005).
