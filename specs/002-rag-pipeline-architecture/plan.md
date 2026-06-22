# Implementation Plan: RAG Engine Architecture & Pipeline Flow Document

**Branch**: `002-rag-pipeline-architecture` | **Date**: 2026-06-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-rag-pipeline-architecture/spec.md`

## Summary

Produce a single authoritative reference **document** that explains the newsletter RAG engine
(feature `001-may-newsletter-pipeline`) to producers and engineers: the end-to-end pipeline
flow, the inputs and outputs at each layer, the key data structures that move through it, and
a mapping from each stage to the code that implements it. The document is descriptive only —
it changes no pipeline behavior. It is authored in GitHub-flavored Markdown with the flow
illustrated as a Mermaid diagram (diagram-as-code, consistent with the engine's own Principle
IV), sourced from the `001` spec/plan/data-model artifacts as the source of truth, and stored
as a discoverable top-level `docs/rag-engine-architecture.md`. No secrets, API keys, or real
transcript content appear in it.

## Technical Context

**Language/Version**: N/A — deliverable is a GitHub-flavored Markdown document (no application
code); the flow diagram is authored in Mermaid (diagram-as-code)
**Primary Dependencies**: None to author or read beyond a Markdown/Mermaid renderer. Source of
truth is the `001-may-newsletter-pipeline` artifacts (spec.md, plan.md, data-model.md,
contracts/). Mermaid is already the project's diagram convention (Principle IV).
**Storage**: Filesystem — `docs/rag-engine-architecture.md` at repo root, plus this feature's
own spec/plan artifacts under `specs/002-rag-pipeline-architecture/`
**Testing**: None (constitution Principle V — no automated tests). The document is validated by
a reader walkthrough against the spec's Success Criteria (SC-001..SC-006): stage-naming,
input/output completeness, code-location lookup, diagram coverage, and a no-secrets review.
**Target Platform**: The repository — viewable in any Markdown renderer (IDE, GitHub, web)
**Project Type**: Documentation — a single written artifact (no source tree, no services)
**Performance Goals**: A reader can locate the implementing code directory/module for any named
stage in under 1 minute (SC-003); a newcomer can name every stage in order (SC-001)
**Constraints**: No secrets, API keys, or real source/transcript content (FR-015); provider
config referenced by environment-variable names only; flow expressed as diagram-as-code
(Principle IV); document states the engine version/feature and date it describes (FR-003)
**Scale/Scope**: One document covering ~10 pipeline stages (scan/ingest → classify → redact →
chunk/embed/store → retrieve → generate → render → report → archive), plus a code-structure
map and key data-structure summaries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Constitution v3.0.0 — all 9 principles evaluated. This feature produces documentation only and
changes no engine behavior; principles are evaluated for whether the **document** complies and
describes the engine accurately.*

| # | Principle | Status | How this feature complies |
|---|-----------|--------|---------------------------|
| I | Model-Agnostic Core | ✅ | Document accurately describes provider access as isolated behind a config-selected adapter (FR-014); it introduces no provider coupling of its own |
| II | Ingestion Fidelity & Provenance | ✅ | Document enumerates all four input types and the transcript-vs-document distinction, and describes the normalized chunk + provenance (FR-008/FR-009) |
| III | Grounded Generation | ✅ | Document is itself grounded in the `001` artifacts (source of truth); it describes citations/grounding rather than inventing engine behavior |
| IV | Diagrams as Code | ✅ | The required end-to-end flow diagram is authored in Mermaid (diagram-as-code), matching the engine's own convention (FR-005) |
| V | Simplicity & Safeguard-Validated Quality | ✅ | No automated tests; the doc is verified by a reader walkthrough against SC-001..SC-006; single artifact, no added infrastructure |
| VI | Observability & Cost Transparency | ✅ | Not applicable to a static document (no runs/model calls); the doc describes the engine's observability accurately |
| VII | Technical-Only Content Scope | ✅ | Not an engine edition; no classification needed. Content is purely the engineering description requested |
| VIII | Storytelling / Architect Voice | ✅ | Doc leads with a plain-language overview for non-technical readers (FR-002), expanding jargon — consistent with the architect-voice intent |
| IX | Enterprise Publication Governance | ✅ | Not a published newsletter edition (no brand/classification/archive obligations). Privacy constraint applies and is met: FR-015 forbids secrets/keys/raw content in the document |

**Privacy/Security constraints (Content Quality, Privacy & Security)**: The document MUST contain
no API keys, credentials, or verbatim source/transcript content; provider configuration is
referenced by environment-variable name only (FR-015). This is the one hard gate that applies to
a documentation deliverable, and it is enforced by SC-005 (no-secrets review).

**Gate result: PASS — no violations. Complexity Tracking intentionally empty.**

## Project Structure

### Documentation (this feature)

```text
specs/002-rag-pipeline-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output (format, source-of-truth, location, diagram tooling)
├── data-model.md        # Phase 1 output (documentation entities)
├── quickstart.md        # Phase 1 output (how to read/produce/verify the document)
├── contracts/
│   └── document-outline.md   # Required section structure the deliverable MUST follow
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit-specify)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

This feature adds no application code. Its only deliverable is a documentation artifact:

```text
docs/
└── rag-engine-architecture.md   # THE deliverable: overview, end-to-end flow + Mermaid
                                  # diagram, per-layer inputs/outputs, key data structures,
                                  # and stage→code mapping. Describes the engine defined by
                                  # specs/001-may-newsletter-pipeline (source of truth).
```

For reference, the engine the document describes lives at `src/newsletter_engine/` (per the
`001` plan); the document maps each pipeline stage to that tree (e.g., `ingestion/`,
`classification/`, `redaction/`, `retrieval/`, `models/`, `generation/`, `rendering/`,
`report/`, `archive/`, `store/`, `observability/`) plus `prompts/`, `config/`, `Documents/`,
`editions/`, and `archive/`.

**Structure Decision**: Documentation feature — no `src/`, `tests/`, or services are created.
The single deliverable is `docs/rag-engine-architecture.md` (top-level `docs/` chosen for
discoverability by both producers and engineers, rather than burying it under `specs/`). The
`001` feature's artifacts are the authoritative source of truth for everything the document
describes; where implementation and those artifacts diverge, the artifacts win unless the
producer states otherwise (spec Assumptions).

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.
