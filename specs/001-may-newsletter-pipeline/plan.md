# Implementation Plan: May Technical Newsletter — Full Pipeline & Enterprise Template

**Branch**: `001-may-newsletter-pipeline` | **Date**: 2026-06-10 (amended 2026-06-11) | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-may-newsletter-pipeline/spec.md`
(including the 2026-06-11 amendment: no review/approval mechanism, any-LLM provider via
configuration with the supplied Anthropic Claude key, no automated tests, and the generated
May 2026 edition as a required deliverable)

## Summary

Build a command-line, end-to-end RAG pipeline that ingests a month's source folders
(meeting transcripts as .docx, PowerPoint decks; PDFs/Word/text also supported), keeps only
technical content, and generates an enterprise-templated newsletter — narrative
stories in a solution architect's voice, validated Mermaid diagrams, citations to source
locations. The edition is final upon successful generation: an informational run report and
an immutable archive replace the former review/dual-approval workflow. Python 3.12
+ Typer CLI; all model access behind an in-house provider-agnostic adapter now backed by
Anthropic Claude (the supplied key), with the OpenAI adapter retained as a config-switchable
alternative; ChromaDB local vector store with local embeddings; Jinja2 → HTML/PDF
rendering. Closing deliverable: the actual May 2026 edition generated from `Documents/`.
Full decisions in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Typer (CLI), python-docx / python-pptx / pypdf (parsers), ChromaDB
(local vector store + built-in local embedding function), Anthropic SDK and OpenAI SDK
(inside adapter layer only; provider chosen by config), Jinja2 (template),
@mermaid-js/mermaid-cli via Node 18+ (diagram validation/render), Playwright Chromium (PDF),
structlog (run logs)
**Storage**: SQLite (stdlib) for metadata/audit; ChromaDB persistent local for embeddings;
filesystem for outputs and hashed archive
**Testing**: No automated test suite (constitution v3.0.0 Principle V): quality validated
via runtime safeguards, discretionary fixture dry runs, and producer inspection of output
**Target Platform**: Windows 11 workstation (CLI); portable to Linux CI
**Project Type**: Single project — CLI application with library-structured internals
**Performance Goals**: Full monthly run (tens of files) → final edition in < 30 min
(SC-001); ≥95% of valid files ingested without intervention (SC-005)
**Constraints**: Content leaves the machine only to the configured allow-listed provider
(now Anthropic Claude per the supplied key; OpenAI or others swappable via config —
FR-027); embeddings computed locally (no embedding API dependency); API keys only via
environment variables documented in `.env.example`; no raw content in logs; no web UI
**Scale/Scope**: ~tens of source files/month, one edition/month, single-operator CLI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Constitution v3.0.0 (amended 2026-06-11) — all 9 principles evaluated.*

| # | Principle | Status | How the design complies |
|---|-----------|--------|-------------------------|
| I | Model-Agnostic Core | ✅ | `models/` adapter package owns the only provider SDK imports; role→provider/model routing + allow-list in `config/models.yaml`; Anthropic adapter added beside the OpenAI one; provider swap = config only (research R3, R13) |
| II | Ingestion Fidelity & Provenance | ✅ | One parser per input type → normalized `ContentChunk` with source/type/location/time; transcript-vs-document docx detection; skip-and-report on malformed files (R5, data-model) |
| III | Grounded Generation | ✅ | Generation consumes only retrieved eligible chunks; Citation entity links statements→chunks; insufficient support → omit + report; prompts versioned in `prompts/` (R3, R12) |
| IV | Diagrams as Code | ✅ | Mermaid generated as text, locally validated/rendered via mermaid-cli; ≤2 retries then drop+flag in run report; sources stored beside outputs (R7) |
| V | Simplicity & Safeguard-Validated Quality | ✅ | No automated test suite and no review gate; runtime safeguards (classification thresholds, citation checks, diagram validation) + discretionary fixture dry runs + producer inspection via run report; stages independently runnable (R12) |
| VI | Observability & Cost Transparency | ✅ | structlog JSON-lines per run: stage timings, model calls w/ tokens+cost, retrieval diagnostics, routing decisions; cost computable from logs (R11) |
| VII | Technical-Only Content Scope | ✅ | LLM classifier stage before retrieval eligibility; ambiguous → excluded + listed in run report; leakage remediated by fixing the classifier and re-running (R6) |
| VIII | Storytelling / Architect Voice | ✅ | Versioned writer prompts encode narrative arc + voice + jargon expansion; producer spot-checks at their discretion (R12) |
| IX | Enterprise Publication Governance | ✅ | Central versioned Jinja2 template + brand config; classification label from max-restrictive source; alt text + semantic HTML; edition final on successful generation, auto-archived with hashed manifest + run history — no approval step (R8, R10) |

**Privacy constraints**: chunk text never logged (ids only); redaction before generation;
keys in env only (`.env.example` documents variable names; `claudeapi-key.txt` is
git-ignored and its value must move to the environment).
**Gate result: PASS — no violations, Complexity Tracking empty.**

**Post-Phase-1 re-check (2026-06-10)**: design artifacts (data-model.md, contracts/)
introduce no new violations. PASS.

**Amendment re-check (2026-06-11)**: spec amendment removed the review/approval mechanism,
which conflicted with constitution v2.0.0 (Principles V, VII, VIII, IX mandated the human
review gate). The constitution was amended to v3.0.0 at the user's direction (precedent:
the v2.0.0 "no tests" amendment) before this plan update; the table above reflects v3.0.0.
PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-may-newsletter-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── cli-interface.md # CLI command contract
│   └── config-schema.md # configuration + prompts contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/newsletter_engine/
├── cli.py                  # Typer app: run/trace/archive/status (approve/regenerate removed)
├── config.py               # config loading + allow-list validation (fail fast)
├── ingestion/
│   ├── scanner.py          # recursive folder scan, type detection (incl. FR-002a)
│   ├── parsers/            # transcript_docx.py, pptx.py, document.py, text.py
│   └── chunker.py          # normalized ContentChunk emission
├── classification/         # technical/non-technical classifier stage
├── redaction/              # rule-based PII redactor, speaker→role mapping
├── retrieval/              # ChromaDB store, local embeddings, eligibility filters
├── models/                 # ModelProvider protocol + anthropic_adapter.py /
│                           # openai_adapter.py (the only provider SDK imports)
├── generation/             # section writers, diagram generation, citation assembly
├── rendering/
│   ├── templates/          # central enterprise Jinja2 template + print CSS
│   └── render.py           # HTML + Playwright PDF
├── report/                 # informational run report, edition state machine
│                           # (generating → final → archived; was review/ pre-amendment)
├── archive/                # hashed manifest archive (auto-invoked after generation)
├── store/                  # SQLite persistence (entities per data-model.md)
└── observability/          # structlog setup, cost computation, run report

prompts/                    # versioned prompt artifacts (classifier/writer/diagrammer/alt-text)
config/                     # config.yaml, models.yaml, brand.yaml, redaction.yaml
Documents/                  # default source ingest folder (May .docx transcripts present)
editions/                   # per-month outputs (edition renderings, run report)
archive/                    # immutable final editions (written automatically on success)
fixtures/                   # synthetic sample content (transcripts/decks/docs) for
                            # discretionary dry runs (technical + personal mix)
```

**Structure Decision**: Single project. The CLI is the only interface (clarification Q2);
internals are library-structured per pipeline stage so each stage is independently runnable
for manual verification (Principle V) and the adapter layer stays isolated (Principle I).

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.
