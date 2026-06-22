"""Rule-based PII redaction and speaker -> role mapping (FR-009 / FR-019).

Deterministic and local: emails, phone numbers, and configured custom patterns are
replaced before any content reaches generation; transcript speaker names become roles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from newsletter_engine.config import RedactionConfig

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# 8+ digit sequences with phone separators; the charset excludes ':' so transcript
# timestamps never match.
_PHONE_RE = re.compile(r"(?<![\d:])\+?\d[\d ().\-]{6,}\d(?![\d:])")


@dataclass
class RedactionStats:
    emails: int = 0
    phone_numbers: int = 0
    custom: int = 0
    speakers_mapped: int = 0


def _map_speaker(name: str, cfg: RedactionConfig) -> str:
    for known, role in cfg.role_map.items():
        if known.lower() == name.lower():
            return role
    return cfg.default_speaker_role


def redact_text(text: str, cfg: RedactionConfig, stats: RedactionStats) -> str:
    if cfg.emails:
        text, n = _EMAIL_RE.subn("[redacted-email]", text)
        stats.emails += n
    if cfg.phone_numbers:
        text, n = _PHONE_RE.subn("[redacted-phone]", text)
        stats.phone_numbers += n
    for pattern in cfg.custom_patterns:
        text, n = re.subn(pattern, "[redacted]", text)
        stats.custom += n
    return text


def redact_chunks(chunks: list[dict], cfg: RedactionConfig, *, log=None) -> RedactionStats:
    """Redact chunk text in place and replace speaker names with roles."""
    stats = RedactionStats()

    # Collect every transcript speaker so their names can be scrubbed from prose too.
    speakers: dict[str, str] = {}
    if cfg.speaker_handling == "role":
        for chunk in chunks:
            name = chunk["location"].get("speaker")
            if name and name not in speakers:
                speakers[name] = _map_speaker(name, cfg)

    for chunk in chunks:
        text = redact_text(chunk["text"], cfg, stats)
        location = dict(chunk["location"])
        name = location.pop("speaker", None)
        if name is not None:
            role = speakers.get(name, cfg.default_speaker_role)
            location["speaker_role"] = role
            stats.speakers_mapped += 1
        for speaker_name, role in speakers.items():
            if speaker_name and speaker_name in text:
                text = text.replace(speaker_name, role)
        chunk["text"] = text
        chunk["location"] = location

    if log:
        log.info(
            "redaction_complete",
            emails=stats.emails,
            phone_numbers=stats.phone_numbers,
            custom=stats.custom,
            speakers_mapped=stats.speakers_mapped,
        )
    return stats
