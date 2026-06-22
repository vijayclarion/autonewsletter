# Tasks: May Technical Newsletter — 2026-06-11 Amendment (No Review, Any LLM, May Delivery)

**Input**: Design documents from `/specs/001-may-newsletter-pipeline/` (as amended 2026-06-11)
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: NOT INCLUDED — constitution v3.0.0 Principle V requires no automated tests and no
review gate. Quality is validated via runtime safeguards, discretionary fixture dry runs,
and producer inspection of generated output.

**Supersession note**: The original build task list (T001–T039, all completed 2026-06-10/11)
constructed the pre-amendment system and is preserved in git history. The tasks below
modify that existing implementation per the 2026-06-11 spec amendment (no review/approval
mechanism; Anthropic Claude via supplied key with provider-as-configuration; local
embeddings) and deliver the actual May 2026 edition from `Documents/` (FR-028).

**Organization**: Tasks are grouped by user story (US1 = P1 final-edition generation,
US2 = P2 enterprise template, US3 = P3 run report & archive).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3
- All paths are relative to the repository root

---

## Phase 1: Setup (Configuration Surfaces)

**Purpose**: Dependency and configuration changes the amendment requires

- [X] T001 Add `anthropic>=0.40` to `dependencies` in `pyproject.toml` and reinstall the
      package (`pip install -e ".[dev]"`)
- [X] T002 [P] Update `config/models.yaml` per amended contracts/config-schema.md:
      `allowlist: [anthropic, openai]`; `providers.anthropic.api_key_env: ANTHROPIC_API_KEY`;
      roles → `classifier: anthropic/claude-haiku-4-5-20251001`,
      `writer: anthropic/claude-sonnet-4-6`, `diagrammer: anthropic/claude-sonnet-4-6`,
      `embedder: local/all-MiniLM-L6-v2`; add Claude pricing entries
      (claude-sonnet-4-6: 3.00/15.00, claude-haiku-4-5-20251001: 1.00/5.00 per 1M tokens)
- [X] T003 [P] Update `config-dryrun/models.yaml` (mock provider) to the same schema shape
      (local embedder role, no approval-related settings) so offline dry runs keep working
      — verified compatible unchanged (mock is a local provider; schema loads clean)

**Checkpoint**: `pip install -e ".[dev]"` succeeds; config files parse against the loader ✅

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provider adapter, key handling, local embeddings, and the new edition state
machine — required by every story phase below

- [X] T004 Implement the Anthropic adapter (the only module importing the `anthropic` SDK;
      Messages API; returns token usage for cost computation) in
      `src/newsletter_engine/models/anthropic_adapter.py` and register the `anthropic`
      provider in `src/newsletter_engine/models/router.py`
- [X] T005 Implement key loading per research R13 in `src/newsletter_engine/config.py`:
      read `ANTHROPIC_API_KEY` from environment/`.env`; if unset and `claudeapi-key.txt`
      exists at repo root, load the key from that file and log a migrate-to-.env warning;
      never write the key value to logs or config
- [X] T006 Update the fail-fast allow-list rule in `src/newsletter_engine/config.py`:
      the `local` pseudo-provider is always permitted (content never leaves the machine);
      remote providers must still appear in `allowlist` (FR-027)
- [X] T007 Support the `local` embedder role using ChromaDB's built-in default embedding
      function (ONNX `all-MiniLM-L6-v2`) — implemented as a `LocalEmbeddingAdapter` in
      `src/newsletter_engine/models/local_embedding.py` behind the existing router, so
      `retrieval/index.py` needed no change and a remote embedder stays configurable
- [X] T008 Replace the edition state machine in `src/newsletter_engine/store/db.py`:
      `generating → final → archived` (drop `draft`/`in_review`/`approved`); a re-run of a
      `final` edition replaces it; `archived` is terminal (re-runs rejected); remove
      approvals/cycles persistence and rename ReviewRecord storage to RunReport per
      data-model.md (newsletter.db is git-ignored and regenerable — old file deleted,
      schema recreated on next run)

**Checkpoint**: router round-trip incl. anthropic registration succeeds; `newsletter --help`
runs against the updated config ✅

---

## Phase 3: User Story 1 — Generate the Final May Edition (Priority: P1) 🎯 MVP

**Goal**: `newsletter run --month 2026-05` turns `Documents/` content into a **final**
edition (technical-only, narrative stories, validated diagrams, citations) with no
approval step, archived automatically on success.

**Independent Verification**: Run the pipeline against `fixtures/` with the mock provider
and confirm: edition reaches `final` then `archived` in one command; only technical
material appears; corrupt file skipped + reported; no `approve`/`regenerate` command
exists.

- [X] T009 [US1] Update the `run` command in `src/newsletter_engine/cli.py`: on success the
      edition becomes `final` (FR-022) and the archiver is invoked automatically (FR-023);
      remove review-cycle handling; keep the "nothing to publish" empty-content path
- [X] T010 [US1] Rename package `src/newsletter_engine/review/` →
      `src/newsletter_engine/report/` (moving `summary.py`, `trace.py`,
      `classification.py`; updating all imports), and delete
      `src/newsletter_engine/review/approvals.py` and
      `src/newsletter_engine/generation/regenerate.py`
- [X] T011 [US1] Remove the `approve` and `regenerate` commands from
      `src/newsletter_engine/cli.py`; update `status` to print
      `generating | final | archived`, file counts, and informational run-report flags
- [X] T012 [P] [US1] Update the output layout in `src/newsletter_engine/rendering/render.py`
      and the report writer: `editions/<month>/edition/` (was `draft/`) and
      `editions/<month>/report/summary.md` (was `review/summary.md`), per amended
      contracts/cli-interface.md (also renamed `render_draft` → `render_edition`)

**Checkpoint**: fixture dry run produced a final, auto-archived edition end-to-end ✅
(2026-03: 6 ingested / 1 skipped / 26 chunks; 15 technical, 11 excluded; 1 valid diagram;
HTML+PDF rendered; archived with 16 hashed artifacts; re-run of archived edition rejected)

---

## Phase 4: User Story 2 — Enterprise Template (Priority: P2)

**Goal**: The centrally versioned template renders identically post-amendment, with no
review/approval wording anywhere in the output.

**Independent Verification**: Render two fixture editions (different months) and confirm
identical section structure/styling, classification banner, accessibility attributes, and
no "draft"/"pending review" labels.

- [X] T013 [US2] Sweep `src/newsletter_engine/rendering/templates/` and rendered-output
      strings for review/approval-era wording — removed the "(draft for review)" masthead
      marker from `edition.html.j2`; masthead, section order, classification banner, and
      alt-text/semantic-heading behavior unchanged

---

## Phase 5: User Story 3 — Run Report & Archive (Priority: P3)

**Goal**: Every run emits an informational run report (gates nothing) and the immutable
archive is written automatically with run history instead of approval records.

**Independent Verification**: Fixture run with at least one excluded chunk and one failed
diagram → `report/summary.md` lists each with a reason; `archive/<month>/` contains
renderings, diagram sources, run report, prompt/config snapshots, run logs, and a SHA-256
`manifest.json` that verifies; no approvals.json anywhere.

- [X] T014 [US3] Update run-report assembly in `src/newsletter_engine/report/summary.py`:
      informational framing (no approval prompts/checklists), retaining excluded/ambiguous
      chunks, skipped files, insufficient-support sections, and failed diagrams, each with
      its reason (FR-020)
- [X] T015 [US3] Update `src/newsletter_engine/archive/archiver.py`: drop `approvals.json`;
      archive runs automatically from `run` when the edition reaches `final`; keep
      `newsletter archive` as a manual fallback that errors unless the edition is `final`
      and not yet `archived`; manifest hashes cover every artifact (FR-023)

---

## Phase 6: Polish & Delivery

**Purpose**: Verify the amended system offline, update docs, then produce the required
May 2026 edition (FR-028)

- [X] T016 Offline verification: `newsletter run --month 2026-03 --source fixtures
      --config config-dryrun/config.yaml` reached `final` + `archived` with the new output
      paths and report contents; `ruff check src scripts` clean
- [X] T017 [P] Update `README.md` (and any other doc that describes the approve/review
      flow) to the amended single-command workflow and Anthropic/any-provider configuration
- [X] T018 Deliver the May edition (FR-028, SC-001, SC-007): run `newsletter run
      --month 2026-05` against `Documents/` (7 transcript .docx files); confirm
      `editions/2026-05/edition/newsletter.html` + `.pdf`, `report/summary.md`,
      `run-report.json` (with token/cost figures), and a verifying
      `archive/2026-05/manifest.json` are produced
      — **DELIVERED 2026-06-15** (run 764e3d8b) using OpenAI per producer choice: switched
      roles to OpenAI (gpt-4o-mini classifier, gpt-4o writer/diagrammer; local embedder),
      key loaded from git-ignored `openai-key.txt` fallback. Earlier Anthropic attempt was
      **BLOCKED 2026-06-12** (run 9ba68d0d): every Claude call returned "Your credit balance
      is too low to access the Anthropic API" (key authenticated, account had no credits);
      that attempt also surfaced and fixed a real parser gap — Teams exports pack
      "Speaker  0:03\nUtterance" into single paragraphs, so transcript detection failed;
      `transcript_docx.py` now splits paragraphs into logical lines (all 7 files parse as
      transcripts). The OpenAI run produced: 7 ingested / 0 skipped / 1038 chunks
      (445 technical, 491 non-technical, 102 ambiguous); 5 stories; 1 valid diagram, 0 failed;
      HTML+PDF+report rendered; edition reached `final`. Stale fixture `newsletter.db`,
      `.chroma`, and `archive/2026-05` (git-ignored, regenerable) were cleared first since
      a leftover archived `2026-05` blocked the real run; `newsletter archive --month 2026-05`
      then wrote `archive/2026-05/` with 18 hashed artifacts and `verify_manifest` confirmed
      all hashes match. Total OpenAI cost $0.187534.
- [ ] T019 Producer spot-check of the generated May edition (SC-002/SC-003/SC-004/SC-006):
      resolve 20 citations via `newsletter trace --month 2026-05`, confirm zero personal/
      non-technical content, and confirm every architecture/flow story has a captioned,
      alt-texted diagram
      — **Automated pre-checks passed 2026-06-15**, producer visual sign-off still pending:
      `trace` resolves citations to source file + timestamp + speaker role + excerpt
      (verified on [c1] → Architects Innovation Day (4).docx @ 11:01); the rendered HTML
      carries the Cloud-First/FDE diagram with `role="img"` + `aria-label` (alt text) +
      `<figcaption>` (FR-018); section headings are all technical (5 engineering stories,
      no personal/social topics) and the run report lists 491 non-technical + 102 ambiguous
      chunks excluded with reasons. Remaining for producer: eyeball the full 20-citation /
      zero-personal-content pass and final visual approval.

---

## Dependencies

- **Phase 1 → Phase 2 → Phase 3**: strictly ordered (config → adapter/state machine → CLI flow)
- **Phase 4 (US2)** and **Phase 5 (US3)**: depend on Phase 3's rename (T010) and run-flow
  change (T009); US2 (T013) and US3 (T014–T015) are independent of each other
- **Phase 6**: T016 requires all of Phases 2–5; T018 requires T016; T019 requires T018
- Within phases: T002/T003 parallel; T004–T008 sequential except T007 [P]-eligible after
  T004; T012 parallel with T010/T011

## Parallel Execution Examples

- After T001: run T002 and T003 together (different config trees)
- After T009–T011: run T012 (rendering paths) alongside T013 (template sweep)
- T014 and T015 can proceed in parallel (different modules) once T010 lands
- T017 can run any time after T011 (CLI surface fixed)

## Implementation Strategy

**MVP first**: Phases 1–3 alone produce a final, auto-archived edition from fixtures with
the Claude adapter — that is the demonstrable core of the amendment. Phases 4–5 are
cleanup/transparency increments. Phase 6 closes with the real deliverable: the May 2026
edition generated from `Documents/`, which is the user's stated outcome ("Please also
create full newsletter May month from files provided in Documents folder").
