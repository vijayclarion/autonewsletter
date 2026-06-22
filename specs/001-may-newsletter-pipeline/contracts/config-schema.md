# Contract: Configuration Schema

Configuration is the only place provider identity, routing, thresholds, brand, and
policies live (Constitution I, VII, IX; FR-027). Secrets (API keys) come from environment
variables / `.env`, never from these files.

## `config/config.yaml` (root)

```yaml
source_dir: "Documents"          # default ingest folder (FR-001)
output_dir: "editions"
archive_dir: "archive"
classification_default: internal # edition label floor (FR-017)
classifier:
  confidence_threshold: 0.8      # below → ambiguous, excluded + flagged (FR-008)
diagrams:
  max_regeneration_retries: 2    # then drop + flag (FR-013)
```

## `config/models.yaml` (Constitution Principle I, FR-027)

*(Amended 2026-06-11: any LLM provider via configuration; Anthropic Claude is the active
provider per the supplied key; embeddings are computed locally — see research R4/R13.)*

```yaml
allowlist:                       # providers permitted to receive content
  - anthropic                    # active: producer-supplied Claude key
  - openai                       # retained alternative (config switch only)
providers:
  anthropic:
    api_key_env: ANTHROPIC_API_KEY   # fallback: local git-ignored claudeapi-key.txt (R13)
  openai:
    api_key_env: OPENAI_API_KEY
roles:                           # logical role → provider/model routing
  classifier: { provider: anthropic, model: claude-haiku-4-5-20251001 }
  writer:     { provider: anthropic, model: claude-sonnet-4-6 }
  diagrammer: { provider: anthropic, model: claude-sonnet-4-6 }
  embedder:   { provider: local, model: all-MiniLM-L6-v2 }   # ChromaDB built-in, no API
pricing:                         # per-1M-token costs for run reports (FR-024)
  claude-sonnet-4-6:        { input: 3.00, output: 15.00 }
  claude-haiku-4-5-20251001: { input: 1.00, output: 5.00 }
  gpt-4o:      { input: 2.50, output: 10.00 }
  gpt-4o-mini: { input: 0.15, output: 0.60 }
  all-MiniLM-L6-v2: { input: 0, output: 0 }
```

**Rules**: a role MUST NOT reference a remote provider absent from `allowlist` (`local`
is always permitted — content never leaves the machine); startup fails fast on violation.
Environment overrides `LLM_PROVIDER` / `LLM_MODEL` (documented in `.env.example`) take
precedence over the writer-role default. Swapping providers = edit this file + add adapter
if new; nothing else changes.

## `config/brand.yaml` (Principle IX, FR-016)

```yaml
newsletter_title: "Engineering Insights"
logo_path: null                  # pending brand assets → placeholder style + flag
palette: { primary: "#1F3A5F", accent: "#E07B39", text: "#1A1A1A" }
typography: { heading: "Segoe UI", body: "Georgia" }
pending_brand_assets: true       # flagged in run report until assets provided
```

## `config/redaction.yaml` (FR-009)

```yaml
redact:
  emails: true
  phone_numbers: true
  custom_patterns: []            # regexes
speaker_handling: role           # map speaker names → roles (FR-019)
role_map:                        # optional explicit mapping
  "": ""
```

## `prompts/` (versioned artifacts, Principle III)

```
prompts/
├── classifier.v1.md
├── writer-story.v1.md
├── writer-tldr.v1.md
├── diagrammer.v1.md
└── alt-text.v1.md
```

Prompt files are addressed by versioned id; run reports record the ids used
(PipelineRun.prompt_versions). Changing a prompt = new version file + config/PR review.
