# Feature Specification: May Technical Newsletter — Full Pipeline & Enterprise Template

**Feature Branch**: `001-may-newsletter-pipeline`
**Created**: 2026-06-10
**Status**: Draft (amended 2026-06-11)
**Input**: User description: "I want to build technical newsletter for May the content is in
Documents folder. Please build the full pipeline and Newsletter template as per enterprise"
**Amendment (2026-06-11)**: "I dont want any review or approval mechanism now. I provide
folder path in repository which will contain all meeting transcripts, documents, powerpoints
and technical newsletter needs to be created from those files. Also no unit and integration
test case required. Also openai or claude or any other LLM model api key can be used. I will
provide the api-key in .env.example and LLM model. Please also create full newsletter May
month from files provided in Documents folder. I have also specified claude apikey in
claudeapi-key.txt"

## Clarifications

### Session 2026-06-10

- Q: Where is the actual May source content located? → A: The Documents folder consists of
  .docx files which are meeting transcripts. The May edition's source content is meeting
  transcripts delivered as Word (.docx) files, to be placed in the project's `Documents/`
  ingest folder (folder is currently empty; producer will populate it).
- Q: How do the producer and reviewers interact with the system? → A: The producer adds
  folders containing meeting transcripts and PowerPoint presentations into the source
  location and executes the pipeline from the command line; outputs (draft, review summary,
  reports) are produced as files. No web application is in scope.
- Q: Can transcript content be sent to cloud AI providers? → A: Yes — the organization holds
  a ChatGPT (OpenAI) license, so its cloud AI service is the initially allow-listed
  provider; however, the provider may change in the future, so switching providers must not
  require rework beyond configuration.

### Session 2026-06-11 (amendment)

- Q: Is a human review/approval workflow required before an edition is final? → A: No — the
  review and approval mechanism is removed for now. The edition is final upon successful
  generation. Transparency artifacts (excluded content, skipped files, failed diagrams)
  remain as an informational run report; nothing gates finalization.
- Q: Which AI provider is used? → A: Any LLM provider (OpenAI, Anthropic Claude, or another)
  may be used; the provider and model are configuration. The API key is supplied via
  environment variables whose names are documented in `.env.example`. The producer has
  supplied an Anthropic Claude API key (in `claudeapi-key.txt`, which is git-ignored and
  whose value must be moved into the environment, never committed).
- Q: Are automated tests required? → A: No — unit and integration test suites are explicitly
  not required for this feature. Verification is by manual inspection of generated outputs.
- Q: What is the concrete deliverable? → A: Beyond the pipeline itself, the actual full May
  2026 newsletter edition must be generated from the files currently present in the
  `Documents/` folder (seven .docx meeting transcripts).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate the May Edition from Source Content (Priority: P1)

A newsletter producer places May's source material — documents, PowerPoint decks, meeting
transcripts, and plain-text notes — into the designated source content folder and runs the
pipeline. The engine ingests every readable file, keeps only technical content (discussions,
presentations, and technical action items), and produces a complete May newsletter:
narrative feature stories told in a solution architect's voice, supporting diagrams, a TL;DR
summary, a technical action-items section, and source citations — the finished edition, no
approval step required.

**Why this priority**: This is the core value of the product. Without an end-to-end run that
turns raw May content into a finished edition, nothing else (template polish, reporting)
matters. It is independently demonstrable as an MVP.

**Independent Test**: Place a known mixed set of files (at least one document, one PowerPoint,
one meeting transcript, one text note — containing both technical and personal content) into
the source folder, run the pipeline, and verify an edition is produced that contains only the
technical material, in narrative form, with diagrams and citations.

**Acceptance Scenarios**:

1. **Given** the source folder contains valid May files of all four supported types,
   **When** the producer runs the pipeline for the May edition, **Then** a complete newsletter
   edition is generated containing every mandatory section (masthead, TL;DR, feature stories,
   technical action items, references).
2. **Given** a meeting transcript mixing technical discussion with personal updates and small
   talk, **When** the pipeline processes it, **Then** only the technical discussion and
   technical action items appear in the edition and no personal content is present.
3. **Given** a feature story describing an architecture, data flow, or process,
   **When** the edition is generated, **Then** that story includes at least one captioned
   diagram that renders correctly and is referenced from the narrative text.
4. **Given** any factual statement in the generated edition, **When** anyone inspects it,
   **Then** the statement carries a citation that resolves to the specific source file and
   location (page, slide, or transcript timestamp) it came from.
5. **Given** a source file that is corrupt or unreadable, **When** the pipeline runs,
   **Then** the file is reported in a skipped-files list with a reason, and the run completes
   for all remaining files.

---

### User Story 2 - Reusable Enterprise Newsletter Template (Priority: P2)

The organization needs every edition — May and all future months — to look and read the same:
a branded, professional layout following the industry-standard technical newsletter structure,
carrying a confidentiality classification label, and meeting accessibility expectations. The
producer selects the edition month and the template applies the standard structure
automatically; the template is maintained centrally, not per edition.

**Why this priority**: The user explicitly asked for an enterprise-grade template. It is the
contract for what "done" looks like for every edition, but it only becomes visible value once
US1 can fill it with content.

**Independent Test**: Generate an edition with sample content and verify the output matches
the enterprise template: branding elements present, all mandatory sections in order,
classification label shown, diagrams captioned with descriptive alternative text, and
consistent styling for headings, callouts, and code snippets.

**Acceptance Scenarios**:

1. **Given** a generated edition, **When** it is rendered, **Then** it displays the masthead
   (newsletter title, edition number, month/year), the organization's branding, and a
   confidentiality classification label derived from the most restrictive source input.
2. **Given** two editions generated in different months, **When** they are compared,
   **Then** both follow the identical section structure and visual style with no per-edition
   styling deviations.
3. **Given** a reader using assistive technology, **When** they consume the edition,
   **Then** every diagram has descriptive alternative text and the document uses a logical,
   semantic heading hierarchy.
4. **Given** an edition where the pipeline cannot populate a mandatory section (e.g., no
   technical action items found), **When** the edition is produced, **Then** the gap is
   explicitly noted in the edition and the run report rather than silently dropped or filled
   with invented content.

---

### User Story 3 - Transparent Run Report and Archive (Priority: P3)

After each run, the producer can see everything the pipeline excluded or could not do
(ambiguous content excluded by default, skipped files, sections with insufficient source
support, diagrams that failed to render) in an informational run report, and can trace any
statement back to its source. Generated editions are archived with their full history so any
past edition can be reconstructed. There is no review gate, sign-off, or approval step: the
edition is final the moment generation succeeds.

**Why this priority**: Transparency and auditability remain valuable for trust in the output,
but they only have value once editions (US1) in the standard template (US2) exist.

**Independent Test**: Generate an edition from sources containing at least one excluded or
failed item, and verify the run report lists it with a reason and the archived edition
retains the output, source list, and generation history — with no approval step anywhere in
the flow.

**Acceptance Scenarios**:

1. **Given** a generated edition, **When** the producer opens the run report, **Then** they
   see all excluded-as-ambiguous content, all skipped files, all sections noted for
   insufficient support, and all diagrams that failed validation, each with its reason.
2. **Given** anyone questions a statement, **When** they follow its citation, **Then** they
   reach the exact source file and location supporting it.
3. **Given** generation completes successfully, **When** the run ends, **Then** the edition is
   immediately final and archived together with its source list and generation history — no
   approval, sign-off, or review action is required or offered.

---

### Edge Cases

- Source folder is empty or contains no May-relevant content: the pipeline reports "nothing to
  publish" with a clear explanation instead of producing an empty or fabricated edition.
- A file contains exclusively non-technical content (e.g., a social announcement deck): it is
  ingested, classified, fully excluded, and listed in the run report as excluded.
- Content whose technical/non-technical classification is ambiguous: excluded by default and
  listed in the run report, never silently included.
- A diagram repeatedly fails validation after the allowed retries: the edition ships without
  that diagram and the gap is noted in the run report.
- Source files contain personally identifiable information (names, emails, phone numbers):
  the configured redaction policy is applied before any content appears in the edition.
- Duplicate or near-duplicate content across multiple inputs (e.g., the same topic in a deck
  and a transcript): the edition covers the topic once, citing all contributing sources.
- A very large input set for the month: the pipeline completes without manual intervention and
  reports per-file progress and any skipped files.
- Mixed-sensitivity sources (e.g., one confidential document among internal ones): the edition
  inherits the most restrictive classification.
- A Word (.docx) file in the source folder is a generic document rather than a meeting
  transcript: it is parsed as a document, and a transcript-formatted file is never misread as
  a generic document (and vice versa).

## Requirements *(mandatory)*

### Functional Requirements

**Ingestion & Provenance**

- **FR-001**: System MUST ingest source files from a configurable source content folder,
  defaulting to the `Documents` folder at the project root, including files organized in
  subfolders (the producer adds a folder per meeting/topic; ingestion scans recursively and
  records the containing folder as part of provenance).
- **FR-002**: System MUST support four input types: plain text, documents (PDF and Word),
  PowerPoint presentations, and meeting transcripts. Meeting transcripts arrive as Word
  (.docx) files; the May edition's source content consists of such transcript files plus
  PowerPoint presentations.
- **FR-002a**: System MUST distinguish a Word file containing a meeting transcript (speaker
  turns, timestamps) from a generic Word document sharing the same file extension, and parse
  it as a transcript so provenance captures speaker turn and timestamp.
- **FR-003**: System MUST record provenance for every piece of ingested content: source file,
  input type, location within the source (page, slide, timestamp, or speaker turn), and
  ingestion time.
- **FR-004**: System MUST report unreadable or malformed files with a reason and continue
  processing the remaining files; a bad file MUST NOT abort the run.
- **FR-005**: System MUST scope an edition to a stated month (May for the first edition) and
  identify which ingested content belongs to that edition.

**Content Scope & Safety**

- **FR-006**: System MUST classify all ingested content as technical or non-technical before
  it can be used in a newsletter, including only technical discussions, technical
  presentations, and technical decisions/action items.
- **FR-007**: System MUST exclude personal updates, social chatter, HR/administrative
  announcements, and scheduling talk from newsletter output.
- **FR-008**: System MUST exclude content with ambiguous classification by default and list
  it in the run report.
- **FR-009**: System MUST apply the configured redaction policy to personally identifiable
  information before content appears in any edition.

**Generation & Quality**

- **FR-010**: System MUST generate every factual statement from ingested source content and
  attach a citation resolving to that content's provenance; the system MUST NOT fabricate
  content to fill gaps.
- **FR-011**: System MUST write feature stories as narrative storytelling (context → technical
  exploration → outcome/open questions) in a solution architect's voice, expanding jargon and
  acronyms on first use.
- **FR-012**: System MUST include at least one captioned diagram, referenced from the
  narrative, in each feature story covering an architecture, data flow, sequence, or decision.
- **FR-013**: System MUST validate every diagram before the edition is complete; a diagram
  failing validation after bounded retries is dropped and flagged, never published broken.
- **FR-014**: System MUST omit or flag any section for which retrieved source support is
  insufficient rather than inventing content.

**Enterprise Template**

- **FR-015**: System MUST render every edition from a single centrally maintained template
  containing, in order: masthead (title, edition number, month/year), executive summary
  (TL;DR), feature stories, technical action items, and references.
- **FR-016**: Template MUST apply the organization's branding (logo, typography, color
  palette) consistently across editions with no per-edition styling overrides.
- **FR-017**: Every edition MUST display a confidentiality classification label derived from
  the most restrictive classification among its source inputs.
- **FR-018**: Every edition MUST meet accessibility expectations: descriptive alternative text
  for all diagrams, semantic heading structure, and meaning never conveyed by color alone.
- **FR-019**: The technical action items section MUST list decisions and actions with
  technical context and owner roles only — no personal performance commentary.

**Run Report & Audit** *(no review/approval mechanism — amendment 2026-06-11)*

- **FR-020**: System MUST produce an informational run report covering excluded ambiguous
  content, skipped files, insufficiently supported sections, and failed diagrams, each with a
  reason. The report is for transparency only; nothing in it blocks the edition.
- **FR-021**: Anyone reading the edition MUST be able to trace any statement to its source
  file and location via its citation.
- **FR-022**: System MUST treat an edition as final upon successful generation. No review,
  approval, or sign-off step is required, enforced, or offered. *(Replaces the former
  two-approver requirement, removed by the 2026-06-11 amendment.)*
- **FR-023**: System MUST archive generated editions immutably together with their source
  list, generation history, and run-report flags, so any past edition is fully
  reconstructable.
- **FR-024**: System MUST log each pipeline run with stage-level progress and produce a
  per-run summary including processing outcomes and resource cost of the run.

**Operation & Interface**

- **FR-025**: System MUST be operable from the command line: the producer runs a single
  command (specifying the edition month) to execute the full pipeline; no graphical
  application is required or in scope.
- **FR-026**: System MUST write all outputs as files: the rendered edition (web-page-style
  and print-style) and the run report. No sign-off step exists.
- **FR-027**: System MUST support any configured LLM provider (OpenAI, Anthropic Claude, or
  another) with the provider and model selected purely via configuration; switching providers
  MUST require only a configuration change, with no changes to how editions are produced.
  API keys MUST be supplied via environment variables whose names are documented in
  `.env.example`, and MUST never be stored in committed files. The May edition uses the
  Anthropic Claude key supplied by the producer.
- **FR-028**: The system MUST produce the actual May 2026 edition from the files currently in
  the `Documents/` folder as part of delivering this feature; the generated edition is a
  required deliverable, not just the pipeline capability.

### Key Entities

- **Source Document**: A file supplied for an edition (text, document, PowerPoint, or
  transcript); carries file identity, type, edition month, and confidentiality classification.
- **Content Chunk**: A unit of ingested content with provenance (source, location) and a
  technical/non-technical classification with confidence.
- **Newsletter Edition**: A monthly issue (e.g., May 2026) with status (generating, final,
  archived), classification label, and edition number; an edition becomes final upon
  successful generation with no intervening review state.
- **Newsletter Section**: A structural part of an edition (TL;DR, feature story, action items,
  references) with narrative content and flags.
- **Diagram**: A visual generated from declarative text, with caption, alternative text,
  validation status, and the story it belongs to.
- **Citation**: A link from a statement in the edition to the provenance of the supporting
  content chunk(s).
- **Run Report**: The informational record of an edition's generation: excluded content,
  skipped files, insufficiently supported sections, and failed diagrams, each with reasons
  and timestamps. Purely informational — it gates nothing.
- **Pipeline Run**: One execution of the pipeline: inputs processed, files skipped, stages
  completed, and cost summary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A producer can go from a populated source folder to a complete, final May
  edition in a single pipeline run, in under 30 minutes, without manual content editing and
  without any approval step.
- **SC-002**: 100% of factual statements in a generated edition carry citations that resolve
  to a real source location; spot-checking any 20 statements finds zero broken citations.
- **SC-003**: Zero personal updates or non-technical content items appear in a final edition
  (verified by a manual spot-check pass over the May edition).
- **SC-004**: 100% of feature stories describing an architecture, flow, or decision include at
  least one correctly rendering, captioned diagram with alternative text.
- **SC-005**: At least 95% of valid source files in the folder are ingested without manual
  intervention; every skipped file is listed with a reason.
- **SC-006**: A reader can trace any statement to its source in under 1 minute using the
  citation.
- **SC-007**: The full May 2026 edition is generated from the seven transcript files
  currently in `Documents/` and delivered as rendered output files, with its run report and
  archive entry, in a single pipeline run.
- **SC-008**: Two editions generated in different months are structurally identical (same
  sections, same order, same styling) when compared side by side.

## Assumptions

- **Source content location**: The pipeline's default source folder is `Documents/` at the
  project root (`rag-newsletter-engine/Documents/`), which has been created. Per
  clarification, the May content is a set of Word (.docx) meeting transcript files; the
  producer will place them in this folder (the source-folder setting remains configurable
  for other locations).
- **May edition input mix**: The May edition is generated from meeting transcripts (.docx)
  and PowerPoint presentations, organized in folders the producer adds to the source
  location; the remaining supported input types (plain text, PDF/Word documents) must still
  be supported by the pipeline but are not required to produce the May edition.
- **Edition month**: "May" means May 2026, the month preceding the current date (2026-06-10).
- **Audience & distribution**: The newsletter is an internal enterprise communication; the
  deliverable of this feature is a generated, archived edition ready for distribution. Actual
  delivery (email blast, intranet publishing) is out of scope for this feature.
- **Output form**: The edition is produced as a portable, shareable document (web-page-style
  and print-style renderings from the same template).
- **Default classification**: Editions default to "Internal" unless a more restrictive source
  classification applies.
- **Language**: Source content and newsletter output are in English.
- **Cadence**: One edition per month; May is the first edition produced by the system.
- **Branding inputs**: Organization brand assets (logo, typography, palette) will be provided
  before the first edition is finalized; until then the template uses a neutral professional
  placeholder style flagged as pending brand assets.
- **AI provider**: Any LLM provider (OpenAI, Anthropic Claude, or another) may be used;
  provider identity and model are treated as configuration, never as a fixed dependency. The
  May edition runs against Anthropic Claude using the key the producer supplied. API key
  variable names are documented in `.env.example`; actual key values live only in the
  environment (or a local, git-ignored `.env`).
- **Secret handling**: The producer placed a Claude API key in `claudeapi-key.txt` at the
  repo root. That file is git-ignored and must never be committed; its value is to be loaded
  into the environment variable documented in `.env.example`.
- **No automated tests**: Per the 2026-06-11 amendment, no unit or integration test suites
  are required for this feature. Acceptance is verified by manually inspecting the generated
  May edition, run report, and archive against the success criteria.
- **No review workflow**: There are no reviewer or approver roles. The producer is the only
  actor; transparency is provided by the informational run report.
- **Monthly volume**: A month's source set is assumed to be modest (on the order of tens of
  files — meeting transcripts and decks), consistent with the 30-minute end-to-end target in
  SC-001.
