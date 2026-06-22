"""Informational run report (FR-020, amendment 2026-06-11).

Everything the pipeline excluded, skipped, omitted, or dropped is listed here with a
reason, for transparency only — nothing in this report gates or blocks the edition.
"""

from __future__ import annotations

from pathlib import Path


def write_summary(
    *,
    month: str,
    out_path: Path,
    skipped_files: list[dict],          # {path, reason}
    excluded_chunks: list[dict],        # {chunk_id, source_path, location, label, reason}
    omitted_sections: list[dict],       # {topic, reason}
    flagged_sections: list[dict],       # {title, flags}
    failed_diagrams: list[dict],        # {section_title, reason}
    pending_brand_assets: bool,
    notes: list[str] | None = None,     # free-form pipeline warnings (e.g. PDF failure)
) -> Path:
    lines: list[str] = [
        f"# Run Report — {month}",
        "",
        "Items below were excluded, skipped, or flagged by the pipeline, each with its",
        "reason. This report is informational: the edition is final as generated.",
        "",
        "## Skipped files",
        "",
    ]
    if skipped_files:
        for item in skipped_files:
            lines.append(f"- `{item['path']}` — {item['reason']}")
    else:
        lines.append("- None")

    lines += ["", "## Excluded / ambiguous content", ""]
    if excluded_chunks:
        lines.append("| Source | Location | Label | Reason |")
        lines.append("|--------|----------|-------|--------|")
        for item in excluded_chunks:
            lines.append(
                f"| {item['source_path']} | {item['location']} | {item['label']} |"
                f" {item['reason']} |"
            )
    else:
        lines.append("- None")

    lines += ["", "## Sections omitted (insufficient support)", ""]
    if omitted_sections:
        for item in omitted_sections:
            lines.append(f"- **{item['topic']}** — {item['reason']}")
    else:
        lines.append("- None")

    lines += ["", "## Flagged sections", ""]
    if flagged_sections:
        for item in flagged_sections:
            lines.append(f"- **{item['title']}** — flags: {', '.join(item['flags'])}")
    else:
        lines.append("- None")

    lines += ["", "## Failed diagrams (dropped)", ""]
    if failed_diagrams:
        for item in failed_diagrams:
            lines.append(f"- **{item['section_title']}** — {item['reason']}")
    else:
        lines.append("- None")

    if notes:
        lines += ["", "## Pipeline notes", ""]
        for note in notes:
            lines.append(f"- {note}")

    if pending_brand_assets:
        lines += [
            "",
            "## Branding",
            "",
            "- Brand assets are pending (`pending_brand_assets: true`); the edition uses"
            " placeholder styling.",
        ]

    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
