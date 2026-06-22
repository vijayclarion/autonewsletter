"""Edition rendering via the central enterprise template (FR-015/FR-016, Principle IX).

One versioned Jinja2 template renders every edition; brand identity (logo, palette,
typography) is injected from config/brand.yaml. While ``pending_brand_assets`` is true the
masthead uses a placeholder logo style and the run report carries a flag.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup

from newsletter_engine.config import BrandConfig

TEMPLATE_VERSION = "enterprise-v1"


def _md_to_html(body_md: str) -> str:
    """Tiny markdown subset: paragraphs, bullet lists, bold, code, citation anchors."""
    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        text = re.sub(r"\[(c\d+)\]", r'<sup class="citation" id="ref-\1">[\1]</sup>', text)
        return text

    blocks = re.split(r"\n\s*\n", body_md.strip())
    parts: list[str] = []
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        if all(ln.lstrip().startswith(("- ", "* ")) for ln in lines):
            items = "".join(f"<li>{inline(ln.lstrip()[2:].strip())}</li>" for ln in lines)
            parts.append(f"<ul>{items}</ul>")
        elif len(lines) == 1 and lines[0].startswith("> "):
            parts.append(f'<div class="callout">{inline(lines[0][2:])}</div>')
        else:
            parts.append(f"<p>{inline(' '.join(ln.strip() for ln in lines))}</p>")
    return "\n".join(parts)


def _environment() -> Environment:
    return Environment(
        loader=PackageLoader("newsletter_engine.rendering", "templates"),
        autoescape=select_autoescape(["html", "j2"]),
    )


def render_edition(
    *,
    brand: BrandConfig,
    month: str,
    edition_number: int,
    classification_label: str,
    sections: list[dict],
    out_path: Path,
) -> Path:
    """Render sections (dicts with kind/title/body_md/diagrams) through the template."""
    template = _environment().get_template("edition.html.j2")

    section_models = []
    for section in sections:
        diagrams = []
        for diagram in section.get("diagrams", []):
            svg_path = diagram.get("svg_path")
            if not svg_path:
                continue
            diagrams.append(
                {
                    "svg": Markup(Path(svg_path).read_text(encoding="utf-8")),
                    "caption": diagram.get("caption", ""),
                    "alt_text": diagram.get("alt_text") or diagram.get("caption", ""),
                }
            )
        section_models.append(
            {
                "kind": section["kind"],
                "title": section["title"],
                "body_html": Markup(_md_to_html(section["body_md"])),
                "diagrams": diagrams,
            }
        )

    document = template.render(
        brand=brand,
        edition={
            "month": month,
            "number": edition_number,
            "classification_label": classification_label,
        },
        sections=section_models,
        template_version=TEMPLATE_VERSION,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(document, encoding="utf-8")
    return out_path
