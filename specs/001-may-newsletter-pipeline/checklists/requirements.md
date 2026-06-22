# Specification Quality Checklist: May Technical Newsletter — Full Pipeline & Enterprise Template

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-06-10
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- **Amendment validation (2026-06-11)**: Spec re-validated after the 2026-06-11 amendment;
  all checklist items still pass. Changes applied: (1) review/approval mechanism removed —
  US3 reworked to an informational run report + archive, FR-020–FR-023 and FR-026 rewritten,
  edition is final upon successful generation; (2) FR-027 generalized to any configurable
  LLM provider (OpenAI, Anthropic Claude, or other) with keys via environment variables
  documented in `.env.example` (an Anthropic key was supplied in `claudeapi-key.txt`, now
  git-ignored); (3) no unit/integration tests required — recorded as an Assumptions
  constraint, verification is manual inspection; (4) new FR-028 + SC-007 make the generated
  May 2026 edition from the seven `Documents/` transcripts a required deliverable.
  Note: earlier T036/T039 walkthrough notes below reference the now-removed approval gates;
  they are retained as historical record of the pre-amendment behavior.
- Validation passed on first iteration (2026-06-10). No [NEEDS CLARIFICATION] markers were
  needed; ambiguities were resolved with documented defaults in the spec's Assumptions
  section.
- `/speckit-clarify` session 2026-06-10 resolved three high-impact items (recorded in the
  spec's Clarifications section): (1) May source content = .docx meeting transcripts plus
  PowerPoint decks placed in folders under the project `Documents/` ingest location;
  (2) command-line operation with file outputs, no web UI; (3) cloud AI permitted via the
  organization's ChatGPT/OpenAI license, provider swappable via configuration.
- Remaining open item before the May edition can actually run: the producer must populate
  `rag-newsletter-engine/Documents/` with the May transcript/deck folders.
- Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`
- **T025 dry-run outcome (2026-06-11)**: `newsletter run --month 2026-05 --source fixtures
  --config config-dryrun/config.yaml` (offline mock provider) executed end-to-end and met
  all US1 Independent Verification criteria:
  - Draft (`editions/2026-05/draft/newsletter.html`) contains only technical material —
    transcript small talk, the farewell-picnic/social-corner content, and the team-lunch
    reminder were all excluded as non-technical (11 chunks listed with reasons in
    `review/summary.md`); 15 technical chunks were eligible.
  - Every story statement carries a citation anchor ([c1]–[c6]) resolving in the
    References section to source file + location (page/slide/timestamp+role/lines).
  - The corrupt fixture (`fixtures/corrupt.docx`) was skipped and reported with a reason;
    the run continued (FR-004).
  - Speaker names were mapped to roles (Solution Architect / Platform Lead / Data
    Engineer) in provenance and prose (FR-019).
  - Mermaid diagram generated, validated via local mermaid-cli, rendered to SVG with
    caption + alt text, and embedded in the draft; with mermaid-cli absent (first run) the
    diagram was correctly dropped + flagged (`diagram_dropped`) in draft and summary
    (FR-013). Sources stored at `draft/diagrams/*.mmd|*.svg`.
  - Edition state machine verified: draft → in_review on success; re-run transitioned
    in_review → draft → in_review; invalid transitions (draft → archived) rejected.
  - Fail-fast allow-list rule verified: a role routing to a non-allow-listed provider
    aborts startup with a ConfigError (FR-027).
  - `run-report.json` records stages, counts, cost (token/cost computation from
    models.yaml pricing), and prompt versions; `runs/<run-id>/run.jsonl` logs chunk ids
    only, never chunk text.
- **T030 dry-run outcome (2026-06-11)**: editions 2026-05 (full fixtures) and 2026-04
  (subset `fixtures/2026-05-architecture-sync`) rendered through the central
  `enterprise-v1` template (HTML + Playwright PDF):
  - Structural identity (SC-008): identical DOM section sequence in both —
    masthead → `tldr` → `story` → `action_items` → `references` — same brand CSS tokens.
  - Classification banner present ("internal", derived max-restrictive per FR-017).
  - Accessibility (FR-018): diagram figures carry `role="img"` + `aria-label` alt text and
    `figcaption`; semantic hierarchy one `h1` (masthead) + `h2` per section.
  - Brand injection (FR-016): palette/typography from brand.yaml as CSS custom
    properties; `logo_path: null` produced placeholder logo styling and the
    `pending_brand_assets` flag in the review summary.
- **T036 governance walkthrough (2026-06-11)**, on the 2026-05 fixture edition:
  - `trace` resolved citation `924ae743…` to `caching-design-note.pdf` page 1 with excerpt
    (FR-021, SC-006: well under 1 minute).
  - With only the technical approval recorded, `archive` was blocked (exit 1,
    "only approved editions can be archived"); edition stayed `in_review` (FR-022).
  - After the editorial approval the edition became `approved`; `archive` wrote
    `archive/2026-05/` with 19 artifacts (draft HTML/PDF, diagram .mmd/.svg sources,
    review summary, approvals.json, prompt + config snapshots, run logs) and a SHA-256
    `manifest.json`; `verify_manifest` confirmed all hashes, detected a deliberate tamper
    (then re-verified clean after restore), and the edition reached terminal `archived`
    (re-runs rejected).
  - `regenerate` on 2026-04: `in_review` → `draft`, review cycle incremented to 1,
    pipeline re-ran automatically back to `in_review` (SC-007 instrumentation).
- **T039 final validation (2026-06-11)**: `ruff check src scripts` clean; fresh full
  fixture dry run (edition 2026-03) produced HTML + PDF + summary + report with zero
  ambiguous chunks and a valid diagram. Success-criteria walkthrough:
  - SC-001 PASS (fixture scale): one command → reviewable draft (HTML+PDF) in seconds,
    no manual editing. Real May timing to be confirmed on `Documents/` with OPENAI_API_KEY.
  - SC-002 PASS: citation markers are validated against supplied chunk ids; invalid ids
    dropped + flagged; sections with zero surviving citations are omitted + reported.
  - SC-003 PASS (dry-run level): all personal fixture content excluded with reasons;
    final guarantee rests on the reviewer pass at the gate per constitution.
  - SC-004 PASS: story diagram rendered, captioned, with alt text; failure path
    drops + flags `diagram_dropped` so the gate catches gaps.
  - SC-005 PASS: 6/6 valid files ingested (100% ≥ 95%); the corrupt file is the only
    skip, listed with a reason.
  - SC-006 PASS: single `trace` command returns file + location + excerpt.
  - SC-007 PASS: dual approval reached with 0 regeneration cycles (≤ 2); cycle counting
    verified via `regenerate`.
  - SC-008 PASS: two months structurally identical (see T030).
