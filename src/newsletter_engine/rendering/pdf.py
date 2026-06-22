"""Print-style PDF rendering via Playwright Chromium (FR-026, research R8).

Renders the already-produced HTML draft with the embedded print stylesheet — one template,
two renderings, structurally identical editions (SC-008). Local browser only; content
never leaves the machine.
"""

from __future__ import annotations

from pathlib import Path


class PdfRenderError(Exception):
    """PDF rendering failed (browser missing, render error). The HTML draft still stands."""


def render_pdf(html_path: Path, pdf_path: Path) -> Path:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # playwright not installed
        raise PdfRenderError(f"Playwright is not installed: {exc}") from exc

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(Path(html_path).resolve().as_uri())
                page.emulate_media(media="print")
                page.pdf(
                    path=str(pdf_path),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise PdfRenderError(str(exc)) from exc

    if not pdf_path.exists():
        raise PdfRenderError("Chromium produced no PDF output")
    return pdf_path
