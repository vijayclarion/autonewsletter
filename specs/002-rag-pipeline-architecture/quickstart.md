# Quickstart: RAG Engine Architecture & Pipeline Flow Document

**Date**: 2026-06-15
**Plan**: [plan.md](plan.md)

This feature delivers documentation, so there is nothing to install or run. "Quickstart" here
means: how to author the document, and how to verify it once written.

## What gets produced

- **`docs/rag-engine-architecture.md`** — the single deliverable. Structure is fixed by
  [contracts/document-outline.md](contracts/document-outline.md).

## How to author it

1. **Gather the source of truth** (research R1). Read the `001-may-newsletter-pipeline`
   artifacts:
   - `specs/001-may-newsletter-pipeline/spec.md` — FRs, success criteria, entities
   - `specs/001-may-newsletter-pipeline/plan.md` — technical context + the `src/newsletter_engine/`
     project structure (the stage→code mapping comes straight from here)
   - `specs/001-may-newsletter-pipeline/data-model.md` — entity fields + the edition state machine
   - `specs/001-may-newsletter-pipeline/contracts/` — CLI + config behavior
   Confirm module names against the actual `src/newsletter_engine/` tree where it exists.
2. **Write section by section** following the outline contract:
   overview → flow diagram → per-stage detail → data structures → final outputs → code map.
3. **Draw the flow as Mermaid** (research R2): one `flowchart` from source folder to archived
   edition, with edges labelled by the data passed (e.g., "normalized chunks", "eligible
   chunks", "narrative + citations").
4. **Use the per-stage block for every stage** (Purpose / Inputs / Outputs / Consumed by /
   On failure / Code location) and add the summary table.
5. **Keep it clean of secrets** (research R6): provider config by env-var name only; no real
   transcript text; synthetic examples only.

## How to verify it (no automated tests — constitution Principle V)

Walk the document against the success criteria; each maps to an outline section:

| Check | How | Criterion |
|-------|-----|-----------|
| Stages named & ordered | A reader unfamiliar with the project narrates the flow start to finish | SC-001 |
| Inputs/outputs/consumer per stage | Spot-check every stage subsection (or scan the summary table) | SC-002 |
| Find code for a stage < 1 min | Pick a random stage, locate its module via the code map | SC-003 |
| End-to-end diagram | Confirm one Mermaid diagram covers ingest → archive | SC-004 |
| No secrets / real content | Search the doc for keys, `.env` values, and real transcript text | SC-005 |
| Producer understands overview | A non-technical reader paraphrases the flow from section 2 alone | SC-006 |

## Out of scope

- No engine code is changed, refactored, or run; no newsletter edition is generated.
- Keeping the document in sync after future pipeline changes is not part of this feature
  (the document records the engine version/date it reflects).
