# Contract: Command-Line Interface

*(Amended 2026-06-11: `approve` and `regenerate` commands removed with the review/approval
mechanism; `run` now produces a final, automatically archived edition.)*

The CLI is the system's only external interface (FR-025/FR-026). Command: `newsletter`
(console script). All commands exit `0` on success, `1` on operational failure, `2` on
usage error. All output artifacts are files; stdout carries human-readable progress,
`--json` switches the final summary to JSON.

## `newsletter run`

Execute the full pipeline for an edition.

```
newsletter run --month 2026-05 [--source <dir>] [--config <file>] [--json]
```

| Option | Default | Meaning |
|--------|---------|---------|
| `--month` | required | edition month (ISO `YYYY-MM`) |
| `--source` | `Documents/` at project root | source folder, scanned recursively |
| `--config` | `config/config.yaml` | configuration root |

**Behavior**: ingest → classify → redact → index → generate → validate diagrams → render →
archive. Bad files are skipped and reported, never abort the run (FR-004). Empty/
no-eligible-content ends with "nothing to publish" report, exit 0, no edition (edge case).
On success the edition is **final** immediately (FR-022) and is archived automatically
(FR-023) — there is no review or approval step.

**Outputs** (under `editions/<month>/`):

- `edition/newsletter.html` — web-page-style rendering
- `edition/newsletter.pdf` — print-style rendering
- `edition/diagrams/*.mmd|*.svg` — diagram sources + rendered assets
- `report/summary.md` — informational run report: skipped files, excluded/ambiguous
  content, insufficient-support sections, failed diagrams, each with reason (FR-020);
  gates nothing
- `run-report.json` — stages, counts, cost (FR-024)

Plus `archive/<month>/` written automatically (see `newsletter archive`).

Edition status after success: `final` → `archived`.

## `newsletter trace`

Resolve a citation to its source (FR-021).

```
newsletter trace --month 2026-05 --citation <citation-id>
```

Prints source file, location (page/slide/timestamp+speaker role), and the supporting
chunk text excerpt.

## `newsletter archive`

Re-run archiving manually (normally automatic at the end of `run`; useful if the
automatic step was interrupted).

```
newsletter archive --month 2026-05
```

Writes `archive/<month>/` containing rendered outputs, diagram sources, run report,
prompt/config versions, run logs, and `manifest.json` with SHA-256 hashes of every
artifact (FR-023). Errors if the edition is not `final` or is already `archived`.
Edition becomes `archived` (terminal; re-runs of an archived edition are rejected).

## `newsletter status`

```
newsletter status --month 2026-05 [--json]
```

Prints edition state (`generating` | `final` | `archived`), file counts, and outstanding
informational flags from the run report.
