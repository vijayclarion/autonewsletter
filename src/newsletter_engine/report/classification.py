"""Edition classification-label derivation (FR-017, constitution Principle IX).

The edition's label is the most restrictive label across its ingested sources, floored at
the configured default.
"""

from __future__ import annotations

_RESTRICTIVENESS = {"public": 0, "internal": 1, "confidential": 2}


def derive_label(source_labels: list[str], default: str = "internal") -> str:
    """Return the max-restrictive label over sources, never below ``default``."""
    candidates = [label for label in source_labels if label in _RESTRICTIVENESS]
    candidates.append(default)
    return max(candidates, key=lambda label: _RESTRICTIVENESS[label])
