# Newsletter Engine

A command-line RAG pipeline that turns a month's meeting transcripts, slide decks, and
documents into an enterprise-templated technical newsletter — narrative stories in a
solution architect's voice, validated Mermaid diagrams, citations back to source
locations. The edition is **final upon successful generation** and is archived
automatically with a hashed manifest; an informational run report documents everything
the pipeline excluded or skipped. There is no review or approval step.

For a stage-by-stage walkthrough of how the engine works — the pipeline flow, the inputs and
outputs at each layer, the key data structures, and a map from each stage to its code — see
[`docs/rag-engine-architecture.md`](docs/rag-engine-architecture.md).

All work is governed by the project constitution:
[`.specify/memory/constitution.md`](.specify/memory/constitution.md) (v3.0.0).
Feature spec, plan, and design artifacts live in
[`specs/001-may-newsletter-pipeline/`](specs/001-may-newsletter-pipeline/), including the
[quickstart](specs/001-may-newsletter-pipeline/quickstart.md).

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
npm install -g @mermaid-js/mermaid-cli   # local Mermaid validation/rendering
playwright install chromium              # print-style PDF rendering
Copy-Item .env.example .env              # then put ANTHROPIC_API_KEY in .env
```

Any LLM provider works via configuration (`config/models.yaml`); the active setup routes
to Anthropic Claude. If `ANTHROPIC_API_KEY` is unset but a git-ignored
`claudeapi-key.txt` exists at the repo root, the key is loaded from it with a warning —
migrate it to `.env`. Embeddings are computed locally (no embedding API or second key).

## Command reference

| Command | Purpose |
|---------|---------|
| `newsletter run --month 2026-05 [--source <dir>] [--config <file>] [--json]` | Full pipeline: ingest → classify → redact → index → generate → diagrams → render HTML+PDF → run report → **auto-archive**. Edition becomes `final`, then `archived`. |
| `newsletter trace --month 2026-05 --citation <id>` | Resolve a citation (ids listed in the edition's References section) to source file, location, and excerpt. |
| `newsletter archive --month 2026-05` | Manual retry of the automatic archive step (only needed if it was interrupted). Terminal state. |
| `newsletter status --month 2026-05 [--json]` | Edition state (`generating` \| `final` \| `archived`), file counts, informational flags. |

Outputs land under `editions/<month>/`: `edition/newsletter.html`, `edition/newsletter.pdf`,
`edition/diagrams/*.mmd|*.svg`, `report/summary.md` (informational run report), and
`run-report.json`. The immutable archive is written to `archive/<month>/` with a SHA-256
`manifest.json`. Per-run JSON-lines logs are written to `runs/<run-id>/run.jsonl`
(chunk ids only — never content).

## Offline dry run (no API key)

The pipeline can be exercised end-to-end against synthetic sample content using a local
deterministic mock provider — nothing leaves the machine:

```powershell
python scripts/make_fixtures.py     # one-time fixture generation
newsletter run --month 2026-03 --source fixtures --config config-dryrun/config.yaml
```

See [`fixtures/README.md`](fixtures/README.md) for what each fixture should produce.

## Configuration

| File | Holds |
|------|-------|
| `config/config.yaml` | Source/output/archive folders, classifier threshold, diagram retries |
| `config/models.yaml` | Provider allow-list, role→provider/model routing, pricing (FR-027: a role routing to a non-allow-listed remote provider aborts startup; the `local` embedder needs no key) |
| `config/brand.yaml` | Newsletter title, logo, palette, typography (`pending_brand_assets` flags placeholder styling) |
| `config/redaction.yaml` | PII redaction rules and speaker→role mapping |
| `prompts/*.md` | Versioned prompt artifacts; run reports record the versions used |

Secrets (e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) live only in `.env` / environment
variables — never in committed files.
