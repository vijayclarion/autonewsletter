"""Mermaid diagram generation with local validation (constitution Principle IV, FR-012/013/018).

Diagrams are generated as Mermaid text, validated/rendered to SVG locally via
``@mermaid-js/mermaid-cli`` (``mmdc``), retried at most ``max_retries`` times with the
validation error fed back, then dropped + flagged. Sources are stored beside the SVGs.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from newsletter_engine.models.provider import ModelCallError
from newsletter_engine.models.router import ModelRouter

_RENDER_TIMEOUT_SECONDS = 120


@dataclass
class DiagramResult:
    needed: bool
    status: str = "valid"            # valid | failed
    mermaid_src: str = ""
    caption: str = ""
    alt_text: str = ""
    svg_path: Path | None = None
    mmd_path: Path | None = None
    failure_reason: str = ""


def find_mmdc() -> str | None:
    for name in ("mmdc", "mmdc.cmd"):
        found = shutil.which(name)
        if found:
            return found
    return None


def render_mermaid(src: str, mmd_path: Path, svg_path: Path, mmdc: str) -> tuple[bool, str]:
    mmd_path.parent.mkdir(parents=True, exist_ok=True)
    mmd_path.write_text(src, encoding="utf-8")
    try:
        proc = subprocess.run(
            [mmdc, "-i", str(mmd_path), "-o", str(svg_path), "-q"],
            capture_output=True,
            text=True,
            timeout=_RENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, "mermaid-cli timed out"
    if proc.returncode != 0 or not svg_path.exists():
        error = (proc.stderr or proc.stdout or "unknown mermaid-cli error").strip()
        return False, error[:500]
    return True, ""


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "diagram"


def generate_for_section(
    *,
    section_title: str,
    body_md: str,
    router: ModelRouter,
    diagrammer_prompt: str,
    alt_text_prompt: str,
    max_retries: int,
    diagrams_dir: Path,
    log=None,
) -> DiagramResult | None:
    """Generate, validate, and render one diagram for a story section.

    Returns ``None`` when the diagrammer decides no diagram is warranted.
    """
    mmdc = find_mmdc()
    messages = [
        {"role": "system", "content": diagrammer_prompt},
        {"role": "user", "content": json.dumps({"title": section_title, "body_md": body_md})},
    ]

    last_error = ""
    mermaid_src = ""
    caption = ""
    for attempt in range(1, max_retries + 2):  # first try + max_retries regenerations
        try:
            response = router.chat("diagrammer", messages, json_mode=True)
            parsed = json.loads(response.text)
        except (ModelCallError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            if log:
                log.warning("diagram_generation_failed", attempt=attempt, error=last_error)
            continue

        if not parsed.get("needed"):
            return None
        mermaid_src = parsed.get("mermaid", "")
        caption = parsed.get("caption", "")
        if not mermaid_src:
            last_error = "diagrammer returned no mermaid source"
            continue

        slug = _slug(section_title)
        mmd_path = diagrams_dir / f"{slug}.mmd"
        svg_path = diagrams_dir / f"{slug}.svg"

        if mmdc is None:
            last_error = "mermaid-cli (mmdc) not installed — cannot validate diagram"
            break

        ok, error = render_mermaid(mermaid_src, mmd_path, svg_path, mmdc)
        if ok:
            alt_text = _alt_text(router, alt_text_prompt, mermaid_src, caption, log)
            if log:
                log.info("diagram_validated", section=section_title, attempt=attempt)
            return DiagramResult(
                needed=True,
                status="valid",
                mermaid_src=mermaid_src,
                caption=caption,
                alt_text=alt_text,
                svg_path=svg_path,
                mmd_path=mmd_path,
            )

        last_error = error
        if log:
            log.warning(
                "diagram_validation_failed", section=section_title, attempt=attempt, error=error
            )
        messages.append({"role": "assistant", "content": response.text})
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {"validation_error": error, "instruction": "Fix the Mermaid syntax error."}
                ),
            }
        )

    # Exhausted: drop + flag (FR-013)
    return DiagramResult(
        needed=True,
        status="failed",
        mermaid_src=mermaid_src,
        caption=caption,
        failure_reason=last_error or "diagram generation failed",
    )


def _alt_text(router: ModelRouter, prompt: str, mermaid_src: str, caption: str, log) -> str:
    try:
        response = router.chat(
            "diagrammer",
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps({"mermaid": mermaid_src, "caption": caption})},
            ],
            json_mode=True,
        )
        return json.loads(response.text).get("alt_text", "")
    except (ModelCallError, json.JSONDecodeError) as exc:
        if log:
            log.warning("alt_text_failed", error=str(exc))
        return caption  # caption is better than nothing for accessibility
