<!--
Sync Impact Report
==================
Version change: 2.0.0 → 3.0.0
Rationale: MAJOR bump — the mandatory human review/approval gate is removed in
a backward-incompatible way at the user's direction (spec amendment
2026-06-11: "I dont want any review or approval mechanism now"). Editions are
final upon successful generation; the dual-approver requirement, review state,
and review-gate enforcement language are removed from Principles V, VII, VIII,
IX, the Format Standards, and the Privacy constraints. Transparency is
preserved via the informational run report and the immutable archive.

Modified principles:
- V: "Simplicity & Review-Validated Quality" → "Simplicity & Safeguard-
  Validated Quality" (review gate replaced by runtime safeguards + producer
  inspection)
- VII: review-gate leakage blocking → remediate-and-re-run after generation;
  ambiguous chunks listed in the run report instead of flagged for review
- VIII: editorial-approver verification → versioned prompts + discretionary
  producer spot-checks
- IX: "Approval & cadence" → "Finality & cadence" (no approvers; edition final
  on successful generation); archival keeps run history instead of approval
  history

Added sections: None
Removed sections: None (principles replaced in place; numbering preserved)

Templates requiring updates:
- .specify/templates/plan-template.md — ✅ compatible (generic gate)
- .specify/templates/spec-template.md — ✅ compatible
- .specify/templates/tasks-template.md — ✅ compatible
- specs/001-may-newsletter-pipeline/plan.md — ✅ updated (Constitution Check
  re-evaluated against v3.0.0)
- specs/001-may-newsletter-pipeline/research.md — ✅ R2/R3/R4/R6/R10/R12
  updated; R13 added (Anthropic adapter + local embeddings)
- specs/001-may-newsletter-pipeline/data-model.md — ✅ state machine +
  RunReport entity updated
- specs/001-may-newsletter-pipeline/contracts/ — ✅ approve/regenerate removed,
  models.yaml schema generalized
- specs/001-may-newsletter-pipeline/quickstart.md — ✅ approval steps removed
- specs/001-may-newsletter-pipeline/tasks.md — ⚠ pending regeneration via
  /speckit-tasks

Follow-up TODOs: None
-->

# Multi-Model RAG Newsletter Engine Constitution

## Core Principles

### I. Model-Agnostic Core (Multi-Model by Contract)

Every interaction with a language model, embedding model, or vision model MUST go
through a provider-agnostic interface owned by this project. No module outside the
model-adapter layer may import a provider SDK or reference a provider-specific model
name. Model selection, routing (e.g., cheap model for extraction, strong model for
synthesis), and fallback order MUST be driven by configuration, not code changes.
Adding a new model provider MUST require only a new adapter plus configuration —
zero changes to ingestion, retrieval, or generation logic.

**Rationale**: The engine's value is orchestrating multiple models; hard-coding any
one provider makes routing, cost optimization, and provider outage fallback
impossible without rewrites.

### II. Ingestion Fidelity & Provenance

Each supported input type — plain text, documents (PDF/DOCX), PowerPoint (PPTX), and
meeting transcripts — MUST have a dedicated parser that emits a single normalized
intermediate representation (chunks + metadata). Every chunk MUST carry provenance
metadata: source identifier, input type, location (page, slide, timestamp, or
speaker turn), and ingestion time. Parsers MUST degrade gracefully: a malformed
file is reported and skipped with a structured error, never silently dropped and
never allowed to abort a batch. Supporting a new input format MUST require only a
new parser that targets the same intermediate representation.

**Rationale**: Newsletter claims must be traceable back to a slide, page, or spoken
moment; a uniform representation keeps retrieval and generation independent of how
content arrived.

### III. Grounded Generation (No Unattributed Claims)

All factual statements in a generated newsletter MUST be grounded in retrieved
source chunks. Every newsletter section MUST retain machine-readable citations
linking generated text to the provenance metadata of its supporting chunks. If
retrieval returns insufficient or low-confidence context for a requested topic, the
engine MUST omit the section or flag it for human review — it MUST NOT fabricate
content to fill the gap. Generation prompts and retrieval parameters MUST be
versioned artifacts in the repository, not inline strings.

**Rationale**: A technical newsletter trades on accuracy; hallucinated content
destroys reader trust and is the single highest product risk for a RAG system.

### IV. Diagrams as Code

All diagrams MUST be generated as declarative text (Mermaid as the default;
PlantUML permitted where Mermaid is insufficient) and MUST be syntax-validated and
test-rendered before a newsletter is considered complete. A diagram that fails
validation MUST trigger a bounded regeneration retry; after exhausting retries the
newsletter MUST ship without the diagram (with a flag for human review) rather than
with a broken one. Diagram source MUST be stored alongside the newsletter output so
diagrams are reproducible and editable.

**Rationale**: Text-based diagrams are verifiable, diffable, and regenerable by
models; binary image generation is not testable and cannot be source-controlled
meaningfully.

### V. Simplicity & Safeguard-Validated Quality

Automated test cases — including unit tests, integration tests, and test-first (TDD)
workflows — are NOT required for this project. There is likewise no human review or
approval gate. Quality is validated through three mechanisms instead: (a) runtime
safeguards built into the pipeline itself (classification confidence thresholds,
citation resolution checks, diagram syntax validation), (b) fixture-based dry runs
executed at the implementer's discretion, and (c) the producer's discretionary
inspection of generated output, supported by the informational run report
(Principle IX). Components MUST remain small and independently runnable so manual
verification stays practical, and a defect fix MUST be verified by re-running the
affected pipeline stage on representative input before it is considered resolved.

**Rationale**: The team prioritizes delivery speed for this internal tool;
correctness risk is mitigated by safeguards enforced inside the pipeline itself and
by transparency artifacts (run report, citations, archive) rather than by an
automated test suite or a manual approval workflow.

### VI. Observability & Cost Transparency

Every pipeline run MUST emit structured logs covering: stage timings, model
invocations (provider, model, token counts, latency, cost estimate), retrieval
diagnostics (query, chunk ids, scores), and routing/fallback decisions. Every
generated newsletter MUST be traceable to the exact pipeline run, model versions,
prompt versions, and source documents that produced it. Per-run cost MUST be
computable from logs alone.

**Rationale**: Multi-model routing decisions and RAG quality cannot be debugged or
cost-optimized without per-stage, per-model visibility.

### VII. Technical-Only Content Scope (NON-NEGOTIABLE)

The newsletter MUST contain only technical content: technical discussions, technical
presentations, and technical decisions or action items raised for discussion.
Ingested content MUST pass through a classification stage that labels each chunk as
technical or non-technical before it becomes eligible for retrieval and generation.
Non-technical content — personal updates, social chatter, HR or administrative
announcements, scheduling talk, and small talk in meeting transcripts — MUST be
excluded from newsletter output. Chunks whose classification is ambiguous MUST be
excluded by default and listed with reasons in the run report rather than included.
Scope leakage discovered in a generated edition MUST be remediated by correcting
the classification stage and re-running the edition.

**Rationale**: Source inputs (especially meeting transcripts) mix technical substance
with personal and administrative noise; without an enforced, tested filter the
newsletter's technical authority is diluted and confidential personal remarks could
leak into distributed content.

### VIII. Storytelling Clarity in a Solution Architect's Voice

Newsletters MUST be written as narrative storytelling, not bullet dumps: each
section presents context (the problem or situation), the technical exploration
(what was discussed, presented, or decided), and the outcome or open questions —
in that order. The writing voice MUST be that of a solution architect: authoritative
but accessible, explaining the "why" behind decisions and trade-offs, connecting
implementation detail to architectural intent. Content MUST be easy to understand:
jargon and acronyms are expanded on first use, and complex flows are accompanied by
an appropriate diagram (Principle IV) rather than dense prose. The voice and
narrative requirements MUST be encoded in versioned generation prompts; adherence
MAY be spot-checked by the producer on generated output at their discretion.

**Rationale**: A newsletter is read voluntarily; storytelling with an architect's
framing is what makes technical material engaging and digestible for a mixed
technical audience, and unversioned "tone by vibes" cannot be tested or maintained.

### IX. Enterprise Publication Governance

Every newsletter edition MUST meet enterprise publication standards before release:

- **Brand consistency**: editions MUST render from a centrally versioned template
  implementing the organization's brand guidelines (logo, typography, color
  palette); per-edition styling overrides are prohibited.
- **Confidentiality classification**: every edition MUST carry an explicit
  classification label (e.g., Internal, Confidential, Public) derived from the
  most restrictive classification of its source inputs; distribution lists MUST
  be validated against that label before release.
- **Accessibility**: output MUST satisfy WCAG 2.1 AA — every diagram carries
  descriptive alternative text generated from its diagram-as-code source,
  heading structure is semantic, and color is never the sole carrier of meaning.
- **Audit & archival**: published editions MUST be immutably archived with their
  full traceability record (Principle VI) and run history; an edition, its
  sources, and its generation history MUST be reconstructable for any past
  release.
- **IP & licensing compliance**: third-party content (text, images, code
  snippets) MUST NOT appear without verified license compatibility and
  attribution; internal source material is cited per Principle III.
- **Finality & cadence**: an edition is final upon successful generation with
  all runtime safeguards passing — no approval or sign-off step exists. An
  informational run report MUST accompany every edition for transparency, and
  editions MUST follow a declared publication cadence — an edition whose
  generation fails its runtime safeguards is delayed or skipped, never published
  broken.

**Rationale**: In an enterprise, a newsletter is a governed communication channel:
brand, confidentiality, accessibility, and licensing failures create legal and
reputational risk that outweighs any single edition, so release controls must be
constitutional rather than discretionary.

## Newsletter Format Standards

Every generated newsletter MUST follow the industry-standard technical newsletter
structure, rendered as a clean, consistently styled document:

- **Masthead**: newsletter title, edition number, and date.
- **Executive summary (TL;DR)**: 3–5 sentences a reader can absorb in under a
  minute, covering the edition's key technical takeaways.
- **Feature stories**: one section per major technical topic, each following the
  narrative arc required by Principle VIII (context → exploration → outcome).
- **Diagrams**: each feature story covering an architecture, data flow, sequence,
  or decision MUST include at least one appropriate diagram (Principle IV);
  diagrams MUST carry captions and be referenced from the narrative text.
- **Technical action items**: a dedicated section listing decisions taken and
  actions raised for discussion, each with technical context and owner role
  (roles only — no personal performance commentary, per Principle VII).
- **Further reading / references**: citations resolved from provenance metadata
  (Principle III), formatted as a closing reference list.
- **Layout hygiene**: consistent heading hierarchy, short paragraphs (≤5
  sentences), no orphan headings, and a single visual style for callouts and
  code snippets across all editions.

Deviations from this structure for a given edition MUST be flagged in the run
report; the engine MUST NOT silently invent new sections or drop mandatory ones.

## Content Quality, Privacy & Security Constraints

- Meeting transcripts and uploaded documents are confidential business inputs.
  They MUST NOT be sent to any model provider not explicitly allow-listed in
  configuration, and MUST NOT appear verbatim in logs (provenance metadata and
  chunk identifiers are logged instead of raw content).
- Personally identifiable information detected in transcripts (names, emails,
  phone numbers) MUST be handled per a configurable redaction policy before
  newsletter publication.
- API keys and provider credentials MUST live in environment configuration or a
  secrets manager — never in source, fixtures, or logs.
- Generated newsletters are final upon successful generation; the informational
  run report documents every exclusion, skip, and gap so the producer can audit
  any edition after the fact. No human review gate exists.
- Source documents and intermediate representations MUST have a defined retention
  policy; deletion of a source MUST be propagable to derived chunks and indexes.

## Development Workflow & Quality Gates

- All work follows the Spec Kit flow: constitution → `/speckit-specify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`. Plans MUST pass the
  Constitution Check gate against this document before Phase 0 research.
- Every PR MUST state which principles it touches and how compliance is
  maintained; reviewers MUST block merges that violate a principle without a
  Complexity Tracking justification in the plan.
- Automated tests and CI test gates are optional (Principle V); behavior is
  validated through discretionary dry runs and producer inspection of generated
  output. Linting/static checks MAY run in CI at the team's discretion.
- Prompt, routing-config, and evaluation-set changes are code: they require PR
  review and version history like any other change.
- Simplicity default: start with the fewest models, stores, and services that
  satisfy the spec (YAGNI); added infrastructure requires written justification.

## Governance

This constitution supersedes all other development practices for this project.
Where guidance conflicts, this document wins.

- **Amendments**: Proposed via PR modifying this file, including a Sync Impact
  Report, rationale, and updates to any dependent templates
  (`.specify/templates/*.md`). Amendments require approval from a project
  maintainer before merge.
- **Versioning**: Semantic versioning of this document. MAJOR for removing or
  redefining a principle in a backward-incompatible way; MINOR for adding a
  principle or materially expanding guidance; PATCH for clarifications and
  wording fixes.
- **Compliance review**: Every `/speckit-plan` run re-evaluates the Constitution
  Check gate against the current version. Deviations discovered during
  implementation MUST be recorded in the plan's Complexity Tracking table or
  remediated before merge.

**Version**: 3.0.0 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-06-11
