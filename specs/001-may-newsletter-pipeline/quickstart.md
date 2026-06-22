# Quickstart: May Technical Newsletter

*(Amended 2026-06-11: no review/approval steps; Anthropic Claude is the active provider.)*

## Prerequisites

- Python 3.12+
- Node.js 18+ (for `@mermaid-js/mermaid-cli` diagram validation/rendering)
- An LLM API key — Anthropic Claude (supplied) or OpenAI, selected via configuration

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
npm install -g @mermaid-js/mermaid-cli
playwright install chromium          # print-style PDF rendering
Copy-Item .env.example .env          # then put ANTHROPIC_API_KEY in .env
```

The producer-supplied key in `claudeapi-key.txt` (git-ignored) is picked up automatically
if `ANTHROPIC_API_KEY` is not set, with a warning to migrate it to `.env`.

## Produce the May edition

1. May's source content is already in `Documents\` (seven .docx meeting transcripts);
   additional folders/files (transcripts, decks, documents) can be added the same way:

   ```
   Documents/
   ├── Architects Innovation Day (4).docx
   ├── ...
   └── Tech-Office - All Hands Meeting.docx
   ```

2. Run the pipeline — one command, no approval steps; the edition is final and archived
   automatically on success:

   ```powershell
   newsletter run --month 2026-05
   ```

3. Inspect the outputs under `editions\2026-05\`:
   - `edition\newsletter.html` / `edition\newsletter.pdf` — the final edition
   - `report\summary.md` — informational run report: skipped files, excluded content, flags
   - `run-report.json` — stages, counts, cost

   The immutable archive is written to `archive\2026-05\` with a SHA-256 manifest.

4. Trace any statement back to its source:

   ```powershell
   newsletter trace --month 2026-05 --citation <id-from-edition>
   ```

## Verifying behavior (optional dry run)

No automated test suite is required (constitution v3.0.0). To sanity-check the pipeline
before a real run, execute it against the synthetic sample content:

```powershell
newsletter run --month 2026-05 --source fixtures --config config-dryrun/config.yaml
```

Then confirm in `editions\2026-05\` that personal/small-talk content from the fixtures was
excluded (listed in `report\summary.md`) and citations resolve via `newsletter trace`.
