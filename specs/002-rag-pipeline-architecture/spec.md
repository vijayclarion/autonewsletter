# Feature Specification: RAG Engine Architecture & Pipeline Flow Document

**Feature Branch**: `002-rag-pipeline-architecture`
**Created**: 2026-06-15
**Status**: Draft
**Input**: User description: "I want a document with the RAG engine flow, the code structure, what are the inputs and how pipeline will generate the output at each layer"

## Overview

This feature delivers a single authoritative reference **document** that explains the
newsletter RAG (Retrieval-Augmented Generation) engine to the people who run, maintain, and
extend it. It describes the end-to-end pipeline flow, how the codebase is organized, what
inputs each stage consumes, and what output each stage produces — so a reader can understand
how raw source files become a finished newsletter edition without reading the source code
first. The document describes the existing pipeline (feature `001-may-newsletter-pipeline`);
it does not change the pipeline's behavior.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the End-to-End Pipeline Flow (Priority: P1)

A newsletter producer or engineer new to the project opens the document to learn, in order,
every stage the engine performs — from scanning the source folder to writing the archived
edition — and how data hands off from one stage to the next. They come away able to explain
the full journey of a source file to a published story without opening the code.

**Why this priority**: The flow is the spine of the whole document. Without a clear,
ordered, stage-by-stage walkthrough, the input/output and code-structure sections have
nothing to anchor to. A reader who only gets this story already has a usable mental model.

**Independent Test**: Give the document to someone unfamiliar with the project and ask them
to narrate the path of a single `.docx` transcript from ingestion to the final edition. They
can name each stage in order and state what each stage does, using only the document.

**Acceptance Scenarios**:

1. **Given** the document, **When** a reader looks for the pipeline flow, **Then** they find
   an ordered list (and a visual diagram) of every stage: scan/ingest → classify → redact →
   chunk/embed/store → retrieve → generate (stories, diagrams, citations) → render →
   report → archive.
2. **Given** any two adjacent stages, **When** a reader inspects the handoff between them,
   **Then** the document states what data structure passes from the earlier stage to the
   later one (e.g., normalized content chunks flow from ingestion to classification).
3. **Given** the flow section, **When** a reader needs the big picture quickly, **Then** a
   single end-to-end diagram shows all stages and the data moving between them.

---

### User Story 2 - Know the Input and Output at Each Layer (Priority: P1)

A maintainer wants to reason about, debug, or extend one specific stage. They open the
document, find that stage, and immediately see what it takes in, what it emits, and where
that output goes next — so they can change or troubleshoot one layer in isolation.

**Why this priority**: This is the practical, day-to-day value of the document. Co-equal with
the flow because the flow without explicit per-layer inputs/outputs is too coarse to act on,
and the inputs/outputs without the flow lack ordering.

**Independent Test**: Pick any stage at random (e.g., retrieval). The document states its
inputs (eligible chunks + a query/topic), its outputs (ranked supporting chunks), and the
preceding/following stages — verifiable for every stage without reading code.

**Acceptance Scenarios**:

1. **Given** any pipeline stage in the document, **When** a reader inspects it, **Then** they
   find an explicit list of that stage's inputs, its outputs, and the next stage that
   consumes the output.
2. **Given** the ingestion layer, **When** a reader reviews its inputs, **Then** the document
   names every supported input type (plain text, PDF/Word documents, PowerPoint decks, and
   `.docx` meeting transcripts) and how transcripts are distinguished from generic documents.
3. **Given** the generation layer, **When** a reader reviews its outputs, **Then** the
   document describes the produced artifacts (narrative feature stories, captioned diagrams,
   citations, TL;DR, technical action items) and how citations link statements back to source
   provenance.
4. **Given** the rendering and archive layers, **When** a reader reviews their outputs,
   **Then** the document names the final deliverables (web-style and print-style edition, run
   report, immutable hashed archive entry).

---

### User Story 3 - Map the Flow to the Code Structure (Priority: P2)

An engineer who understands the flow wants to find the code that implements a given stage.
The document maps each pipeline stage to its location in the codebase (directories and
modules) and explains the role of each part, including where provider/model access and prompts
live, so the engineer can navigate from concept to code quickly.

**Why this priority**: Valuable for contributors, but only meaningful once the flow (US1) and
per-layer inputs/outputs (US2) are understood. A reader can get full conceptual value from
US1+US2 without this mapping.

**Independent Test**: For any stage named in the flow, the document points to the
corresponding code location and describes what lives there; a reader can locate the
implementing module from the document alone.

**Acceptance Scenarios**:

1. **Given** the code-structure section, **When** a reader reviews it, **Then** they find the
   project layout (the engine package and its per-stage submodules, plus prompts, config,
   source, editions, and archive locations) with each part's responsibility described.
2. **Given** any stage in the flow, **When** a reader wants the implementing code, **Then**
   the document maps that stage to a specific directory/module.
3. **Given** the document discusses model access, **When** a reader looks for provider
   details, **Then** it explains that all model/provider access is isolated behind an adapter
   layer selected by configuration, and that prompts are versioned artifacts — without
   embedding secrets or API keys.

---

### Edge Cases

- A reader is non-technical (e.g., a producer who only runs the command): the document opens
  with a plain-language overview and end-to-end diagram before any code-level detail, so the
  flow is understandable without engineering background.
- A stage has conditional or failure behavior (e.g., a diagram fails validation after retries,
  a file is unreadable, content is ambiguous): the document describes the input/output for the
  failure path (skipped-files list, dropped-diagram flag, ambiguous-content exclusion), not
  only the happy path.
- The pipeline changes later: the document states the engine version/feature it describes and
  the date, so a reader knows whether it is current.
- A stage produces no output for a given run (e.g., no technical action items found): the
  document explains how that gap is represented rather than implying every stage always emits
  content.

## Requirements *(mandatory)*

### Functional Requirements

**Document Scope & Audience**

- **FR-001**: The document MUST describe the existing newsletter RAG engine pipeline
  (feature `001-may-newsletter-pipeline`) and MUST NOT propose or require changes to that
  pipeline's behavior.
- **FR-002**: The document MUST be understandable by both a non-technical producer (who runs
  the pipeline) and a technical maintainer (who extends it), leading with a plain-language
  overview before code-level detail.
- **FR-003**: The document MUST state which engine version/feature and date it describes, so
  readers can judge whether it is current.

**Pipeline Flow**

- **FR-004**: The document MUST present the full pipeline as an ordered sequence of stages
  covering, at minimum: source scan/ingestion, technical/non-technical classification, PII
  redaction, chunking with local embedding and vector storage, retrieval of eligible content,
  generation (narrative stories, diagrams, citations, TL;DR, action items), rendering, run
  reporting, and archiving.
- **FR-005**: The document MUST include at least one end-to-end visual diagram showing all
  stages and the data flowing between them.
- **FR-006**: For each adjacent pair of stages, the document MUST describe the data that hands
  off from the earlier stage to the later one.

**Inputs & Outputs per Layer**

- **FR-007**: For every stage, the document MUST explicitly state the stage's inputs, its
  outputs, and the stage(s) that consume its output.
- **FR-008**: The document MUST enumerate every supported pipeline input type (plain text,
  PDF/Word documents, PowerPoint decks, and `.docx` meeting transcripts) and explain how a
  transcript `.docx` is distinguished from a generic document `.docx`.
- **FR-009**: The document MUST describe the key data structures that move through the pipeline
  (at minimum the normalized content chunk with its provenance and technical classification,
  and the edition/section/diagram/citation structures), at a conceptual level.
- **FR-010**: The document MUST describe the final output deliverables of the pipeline: the
  rendered edition (web-style and print-style), the informational run report, and the
  immutable archived edition with its source list and generation history.
- **FR-011**: For stages with notable failure or empty-output behavior, the document MUST
  describe the output of that path (skipped files with reasons, ambiguous content excluded,
  diagrams dropped after retries, sections flagged for insufficient support or gaps).

**Code Structure Mapping**

- **FR-012**: The document MUST describe the codebase structure (the engine package, its
  per-stage submodules, and the supporting prompts/config/source/editions/archive locations)
  and the responsibility of each part.
- **FR-013**: The document MUST map each pipeline stage to the code location (directory or
  module) that implements it.
- **FR-014**: The document MUST explain that all model/provider access is isolated behind a
  configuration-selected adapter layer and that prompts are versioned artifacts.

**Safety**

- **FR-015**: The document MUST NOT contain any API keys, secrets, or real source/transcript
  content; provider configuration MUST be described by reference to environment-variable names
  only.

### Key Entities

- **Architecture Document**: The single reference artifact produced by this feature. Contains
  the overview, pipeline flow, per-layer input/output descriptions, data-structure summaries,
  and code-structure mapping. Carries the engine version/feature and date it describes.
- **Pipeline Stage (as documented)**: A described unit of the flow with a name, ordinal
  position, purpose, inputs, outputs, downstream consumer(s), failure/empty-output behavior,
  and a pointer to its implementing code location.
- **Flow Diagram**: The visual representation of the ordered stages and the data passing
  between them, included in the document.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader unfamiliar with the project can, using only the document, correctly
  name every pipeline stage in order and state each stage's purpose.
- **SC-002**: For 100% of the documented stages, the document states the stage's inputs,
  outputs, and downstream consumer.
- **SC-003**: A reader can locate the implementing code directory/module for any named stage
  in under 1 minute using the document's code-structure mapping.
- **SC-004**: The document includes at least one end-to-end diagram covering every stage from
  source ingestion to archived edition.
- **SC-005**: A reviewer confirms the document contains zero secrets, API keys, or real source
  content.
- **SC-006**: A non-technical producer can read the overview section and describe, in their own
  words, how source files become a published edition, without consulting the code.

## Assumptions

- **Subject of the document**: The document describes the pipeline as defined by feature
  `001-may-newsletter-pipeline` (its spec, plan, and data model). If the implementation and
  those artifacts diverge, the artifacts are treated as the source of truth for this
  description unless the producer states otherwise.
- **Format & location**: The deliverable is a single written document (Markdown) stored in the
  repository alongside the feature's other docs; diagrams are expressed as declarative
  diagram-as-code consistent with the rest of the project. Exact filename/location is at the
  author's discretion.
- **Audience**: Primary readers are the newsletter producer and engineers maintaining or
  extending the engine; the document is internal.
- **Scope boundary**: This feature produces documentation only. It does not modify, refactor,
  or re-architect the pipeline, and it does not generate a newsletter edition.
- **Currency**: The document reflects the engine as of the date in its header; keeping it in
  sync after future pipeline changes is out of scope for this feature.
