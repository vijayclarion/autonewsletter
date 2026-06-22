# Phase 0 Research: May Technical Newsletter — Full Pipeline & Enterprise Template

**Date**: 2026-06-10 (amended 2026-06-11 for the no-review / any-LLM spec amendment)
**Plan**: [plan.md](plan.md)

All Technical Context unknowns are resolved below. Each decision lists rationale and the
alternatives considered.

## R1. Language & Runtime

- **Decision**: Python 3.12
- **Rationale**: Best-in-class libraries for every pipeline stage this feature needs —
  Office-format parsing (`python-docx`, `python-pptx`), PDF (`pypdf`), LLM SDKs, vector
  stores, and CLI tooling. The team's environment (Windows, OneDrive paths) is fully
  supported.
- **Alternatives considered**: .NET/C# (team familiarity per neighboring repos, but the
  document-parsing + RAG ecosystem is materially weaker); Node.js (good LLM SDKs, weak
  Office-document parsing).

## R2. CLI Framework

- **Decision**: Typer
- **Rationale**: Spec requires command-line operation (FR-025/FR-026). Typer gives typed
  commands, auto `--help`, and subcommands (`run`, `trace`, `archive`, `status`) with
  minimal boilerplate. *(Amendment 2026-06-11: `approve` and `regenerate` removed with the
  review workflow.)*
- **Alternatives considered**: argparse (more boilerplate, no completion); Click (Typer is
  built on it and adds type hints).

## R3. Model Access Layer (Constitution Principle I)

- **Decision**: In-house `ModelProvider` protocol (chat-completion + embedding methods) in a
  dedicated adapter package. Adapters: `anthropic_adapter.py` (active — the producer
  supplied an Anthropic Claude key) and `openai_adapter.py` (retained, switchable). Model
  routing (which logical role — classifier, writer, diagrammer, embedder — maps to which
  provider/model) lives in `config/models.yaml`; API keys come from environment variables
  documented in `.env.example` (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`), with optional
  `LLM_PROVIDER` / `LLM_MODEL` environment overrides for the writer-role default. Provider
  swap = config edit (plus a new adapter class only for a brand-new provider).
- **Rationale**: Constitution forbids provider SDK imports outside the adapter layer and
  requires config-driven routing; the 2026-06-11 amendment allows "openai or claude or any
  other LLM" and supplies a Claude key, which the adapter design absorbs as configuration.
- **Alternatives considered**: LiteLLM (multi-provider out of the box, but adds a broad
  dependency and overlaps the abstraction the constitution requires us to own); LangChain
  (heavy framework, obscures prompt/citation control needed for grounding).

## R4. Embeddings & Vector Store

- **Decision**: Embeddings computed locally via ChromaDB's built-in default embedding
  function (ONNX `all-MiniLM-L6-v2`), exposed through the same adapter-layer embedding
  role so a remote embedding provider can be configured later. Vector store: ChromaDB in
  local persistent mode (file-backed, in-process, metadata filtering for provenance and
  classification labels). *(Amendment 2026-06-11: previously OpenAI
  `text-embedding-3-small`; Anthropic offers no embedding API and only a Claude key was
  supplied, so the embedder role defaults to the local function — no second API key
  needed, and confidential content never leaves the machine for embedding.)*
- **Rationale**: Monthly corpus is tens of files (spec assumption) — an in-process store is
  ample, has no server to operate, and supports the metadata filters needed to restrict
  retrieval to technical-only, edition-scoped chunks (Principles II, VII). Local embeddings
  at this scale are fast, free, and keep the single-API-key setup workable.
- **Alternatives considered**: FAISS (fast but bare — metadata filtering DIY); sqlite-vec
  (attractive, less mature tooling); pgvector (server overhead violates YAGNI for this
  scale).

## R5. Parsers per Input Type (Constitution Principle II)

- **Decision**:
  - Meeting transcripts (.docx): `python-docx` + transcript detector recognizing
    Teams-export structure (speaker name + timestamp paragraph patterns); chunks by speaker
    turn with timestamp provenance.
  - PowerPoint (.pptx): `python-pptx`; chunks by slide (title + body + notes) with slide
    number provenance.
  - Documents (.pdf/.docx): `pypdf` / `python-docx`; chunks by heading/page with page
    provenance.
  - Plain text (.txt/.md): paragraph chunking with line-range provenance.
  - All parsers emit one normalized `ContentChunk` shape (see data-model.md).
- **Rationale**: FR-002/FR-002a require distinguishing transcript-docx from document-docx;
  structure-based detection (timestamps + speaker turns) is reliable for Teams exports and
  falls back to generic document parsing when patterns are absent.
- **Alternatives considered**: unstructured.io (one-dep-for-everything, but heavyweight,
  slower, and provenance granularity per format is harder to control); Azure Document
  Intelligence (external service — confidential transcripts shouldn't require it for
  formats we can parse locally).

## R6. Technical/Non-Technical Classification (Constitution Principle VII)

- **Decision**: LLM-based chunk classifier (cheap/fast model role via routing config)
  returning label + confidence; threshold from config. Below-threshold or ambiguous →
  excluded and listed in the run report (FR-008). Classifier prompt is a versioned
  artifact; scope leakage found in output is remediated by fixing the classifier and
  re-running (constitution v3.0.0 Principle VII).
- **Rationale**: Personal/technical boundaries in meeting transcripts are contextual —
  keyword rules underfit; an LLM classifier with conservative exclude-by-default behavior
  satisfies Principle VII without a review gate.
- **Alternatives considered**: keyword/regex rules (brittle); fine-tuned local classifier
  (premature for v1 data volume).

## R7. Diagram Generation & Validation (Constitution Principle IV)

- **Decision**: Mermaid as the diagram language, generated by the writer model as fenced
  code; validated and rendered to SVG locally via `@mermaid-js/mermaid-cli` (`mmdc`,
  Node-based, runs headless). Bounded regeneration: 2 retries, then drop + flag (FR-013).
  Alt text generated alongside each diagram from its Mermaid source (FR-018).
- **Rationale**: Mermaid is the de-facto diagrams-as-code standard with the best LLM
  generation quality; local validation avoids sending confidential-derived diagrams to
  external rendering services (e.g., Kroki).
- **Alternatives considered**: PlantUML (allowed by constitution as fallback; requires
  Java); Kroki/mermaid.ink remote rendering (rejected: confidentiality).

## R8. Edition Rendering (FR-015/FR-026, Principle IX)

- **Decision**: Jinja2 enterprise template producing semantic HTML (web-page-style) with an
  embedded print stylesheet; print-style PDF generated from that HTML via Playwright
  headless Chromium. Single template directory, centrally versioned; brand tokens
  (logo path, palette, typography) injected from `config/brand.yaml`.
- **Rationale**: One template → two renderings keeps editions structurally identical
  (SC-008). Playwright's Chromium reuses the same browser engine mermaid-cli already
  installs, and avoids WeasyPrint's GTK pain on Windows.
- **Alternatives considered**: WeasyPrint (GTK dependency on Windows); docx output
  (weak diagram/styling control); LaTeX (overkill, brand styling friction).

## R9. PII Redaction (FR-009)

- **Decision**: Rule-based redactor (emails, phone numbers, configurable name list /
  pattern policy in `config/redaction.yaml`) applied to chunks before generation; speaker
  names mapped to roles (e.g., "Solution Architect") consistent with FR-019.
- **Rationale**: Deterministic, testable, local. Meets the constitution's configurable
  redaction policy without a heavyweight NLP dependency for v1.
- **Alternatives considered**: Microsoft Presidio (more thorough NER-based detection;
  deferred — can be slotted behind the same redaction interface later).

## R10. Persistence, Archive & Audit (FR-023/FR-024, Principles VI, IX)

- **Decision**: SQLite (stdlib `sqlite3`) for chunks, runs, and editions metadata;
  filesystem archive written automatically per final edition (`archive/2026-05/`)
  containing rendered outputs, diagram sources, run report, prompt/config versions, and a
  manifest with SHA-256 hashes for immutability verification. *(Amendment 2026-06-11:
  approval records removed; archiving happens automatically when generation succeeds.)*
- **Rationale**: Zero-ops, file-based, reconstructable; hash manifest gives practical
  immutability without infrastructure.
- **Alternatives considered**: PostgreSQL (server overhead); pure-JSON store (weak querying
  for provenance/citation lookups).

## R11. Observability & Cost (Constitution Principle VI)

- **Decision**: `structlog` JSON-lines log per pipeline run (`runs/<run-id>/run.jsonl`)
  capturing stage timings, model calls (provider, model, tokens, latency, computed cost
  from a price table in config), retrieval diagnostics (query, chunk ids, scores), and
  routing decisions; run report summarizes cost and outcomes (FR-024). Raw chunk text never
  logged — chunk ids only.
- **Alternatives considered**: OpenTelemetry (right for services; overkill for a local CLI
  v1, can be added behind the same logging facade).

## R12. Quality Validation (Constitution Principle V, amended v3.0.0)

- **Decision**: No automated test suite and no human review gate. Quality is validated by
  (a) runtime safeguards in the pipeline (classifier confidence thresholds, citation
  resolution checks, Mermaid syntax validation), (b) discretionary dry runs against
  synthetic sample content in `fixtures/` (transcripts + decks mixing technical and
  personal content), and (c) the producer's discretionary inspection of the generated
  edition, supported by the informational run report.
- **Rationale**: User directive 2026-06-10 ("no need of test case and unit test case")
  removed tests (v2.0.0); user directive 2026-06-11 ("I dont want any review or approval
  mechanism now") removed the review gate (v3.0.0). Delivery speed is prioritized;
  correctness risk is carried by in-pipeline safeguards and transparency artifacts.
- **Alternatives considered**: pytest suites + golden evaluation set (v1.x mandate) and
  the dual-approval review gate (v2.0.0 mandate) — both removed by amendment; either can
  be reinstated later by re-amending the constitution.

## R13. Anthropic Claude Adapter & Key Handling (Amendment 2026-06-11)

- **Decision**: Add `anthropic_adapter.py` implementing the existing `ModelProvider`
  protocol with the official `anthropic` Python SDK (Messages API). Default routing in
  `config/models.yaml` points classifier/writer/diagrammer roles at Anthropic models
  (default `claude-sonnet-4-6`; cheap roles may use `claude-haiku-4-5-20251001`), with
  pricing entries for cost reporting (FR-024). The key is read from `ANTHROPIC_API_KEY`;
  at startup, if `ANTHROPIC_API_KEY` is unset but `claudeapi-key.txt` exists locally, the
  CLI loads the key from that file with a warning to migrate it to `.env` — the file is
  git-ignored and never read into logs or config.
- **Rationale**: The producer supplied a Claude key in `claudeapi-key.txt` and asked for
  provider freedom; the adapter pattern (R3) absorbs this as one new class + config. The
  file fallback makes the supplied key usable immediately without weakening the
  env-only-secrets rule for committed artifacts.
- **Alternatives considered**: Requiring manual `.env` setup only (friction for the
  already-supplied key); LiteLLM proxy (rejected in R3 — broad dependency overlapping the
  constitution-mandated in-house abstraction).
