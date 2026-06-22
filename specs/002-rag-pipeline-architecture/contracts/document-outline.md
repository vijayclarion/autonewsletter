# Contract: Document Outline

**Date**: 2026-06-15
**Plan**: [../plan.md](../plan.md)

The document's "interface" to its readers is its structure. This contract fixes the required
section structure of `docs/rag-engine-architecture.md` so the deliverable is verifiable against
the spec's functional requirements and success criteria. The final document MUST contain these
sections, in this order. Section titles may be reworded; content obligations may not be dropped.

## Required sections

### 1. Header / Metadata  *(FR-003)*
- Title; the feature it describes (`001-may-newsletter-pipeline`); the engine version/feature
  and date the description reflects; a one-line statement that this is descriptive only and
  changes no pipeline behavior.

### 2. Overview (plain language)  *(FR-002, SC-006)*
- 1–3 paragraphs a non-technical producer can read to understand how source files become a
  published edition, before any code-level detail. Expands key jargon (RAG, chunk, embedding,
  retrieval) on first use.

### 3. End-to-End Flow Diagram  *(FR-005, SC-004)*
- One Mermaid diagram covering every stage from source ingestion to archived edition, with
  edges labelled by the data passed between stages. Diagram-as-code (Principle IV).

### 4. Pipeline Stages — detail  *(FR-004, FR-006, FR-007, FR-008, FR-011; SC-001, SC-002)*
- One subsection per stage, in order: Scan & Ingest → Classify → Redact → Chunk/Embed/Store →
  Retrieve → Generate → Render → Report → Archive.
- Each stage subsection MUST use this block:
  - **Purpose** — what the stage does
  - **Inputs** — what it consumes
  - **Outputs** — what it emits
  - **Consumed by** — the next stage(s)
  - **On failure / empty output** — skip/exclude/drop/flag behavior (where applicable)
  - **Code location** — implementing directory/module
- The **Scan & Ingest** subsection MUST enumerate all input types (plain text, PDF/Word
  documents, PowerPoint decks, `.docx` meeting transcripts) and explain how a transcript `.docx`
  is distinguished from a generic document `.docx` (FR-008).
- A summary table listing every stage with its inputs / outputs / consumer SHOULD accompany the
  subsections so SC-002 can be checked at a glance.

### 5. Key Data Structures  *(FR-009)*
- Conceptual summaries of the structures that move through the pipeline: at minimum
  **ContentChunk** (text + provenance/location + technical classification), **Edition**,
  **Section**, **Diagram**, **Citation** — each with its purpose and where in the flow it
  appears. Conceptual only; no schema/DDL required.

### 6. Final Outputs / Deliverables  *(FR-010)*
- The rendered edition (web-style and print-style), the informational run report, and the
  immutable archived edition (with source list + generation history).

### 7. Code Structure Map  *(FR-012, FR-013, FR-014; SC-003)*
- The project layout: the `src/newsletter_engine/` package and its per-stage submodules, plus
  support locations (`prompts/`, `config/`, `Documents/`, `editions/`, `archive/`), each with
  its responsibility.
- An explicit stage → code-location mapping (every stage in section 4 resolves to a directory/
  module).
- A note that all model/provider access is isolated behind a configuration-selected adapter
  layer and that prompts are versioned artifacts (FR-014).

## Cross-cutting constraints  *(FR-015, SC-005)*
- No API keys, secrets, or real source/transcript content anywhere. Provider configuration is
  referenced by environment-variable **name** only. Examples, if any, are synthetic.

## Acceptance (maps to Success Criteria)
- [ ] All stages named and ordered (SC-001) — section 3 + 4
- [ ] Every stage states inputs, outputs, consumer (SC-002) — section 4 (+ summary table)
- [ ] Code location resolvable for any stage in < 1 min (SC-003) — section 7 mapping
- [ ] One end-to-end diagram covers all stages (SC-004) — section 3
- [ ] Zero secrets / real content (SC-005) — cross-cutting review
- [ ] Non-technical reader can describe the flow from the overview (SC-006) — section 2
