"""Technical / non-technical chunk classification (constitution Principle VII, FR-006–008).

Chunks are labelled by the ``classifier`` model role. Anything below the confidence
threshold — or that the model cannot label — becomes ``ambiguous``: excluded from
retrieval and flagged for the review summary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from newsletter_engine.models.provider import ModelCallError
from newsletter_engine.models.router import ModelRouter

_BATCH_SIZE = 15
_MAX_CHUNK_CHARS = 1500


@dataclass
class ClassificationOutcome:
    technical: int = 0
    non_technical: int = 0
    ambiguous: int = 0
    excluded: list[dict] = field(default_factory=list)  # chunk id + label + reason


def classify_chunks(
    chunks: list[dict],
    *,
    router: ModelRouter,
    prompt_text: str,
    confidence_threshold: float,
    log=None,
) -> ClassificationOutcome:
    """Annotate each chunk in place with label / label_confidence / eligible."""
    outcome = ClassificationOutcome()

    for start in range(0, len(chunks), _BATCH_SIZE):
        batch = chunks[start : start + _BATCH_SIZE]
        payload = {
            "chunks": [
                {"index": i, "text": c["text"][:_MAX_CHUNK_CHARS]} for i, c in enumerate(batch)
            ]
        }
        results = _classify_batch(router, prompt_text, payload, log)

        by_index = {r.get("index"): r for r in results}
        for i, chunk in enumerate(batch):
            entry = by_index.get(i)
            if entry is None or entry.get("label") not in ("technical", "non_technical"):
                chunk["label"] = "ambiguous"
                chunk["label_confidence"] = 0.0
            else:
                chunk["label"] = entry["label"]
                chunk["label_confidence"] = float(entry.get("confidence", 0.0))
                if (
                    chunk["label"] == "technical"
                    and chunk["label_confidence"] < confidence_threshold
                ):
                    chunk["label"] = "ambiguous"

            chunk["eligible"] = (
                chunk["label"] == "technical"
                and chunk["label_confidence"] >= confidence_threshold
            )

            if chunk["eligible"]:
                outcome.technical += 1
            elif chunk["label"] == "non_technical":
                outcome.non_technical += 1
                outcome.excluded.append(
                    {"chunk_id": chunk["id"], "label": "non_technical",
                     "reason": "classified as non-technical"}
                )
            else:
                outcome.ambiguous += 1
                outcome.excluded.append(
                    {"chunk_id": chunk["id"], "label": "ambiguous",
                     "reason": "below confidence threshold or unlabelled"}
                )

        if log:
            log.info(
                "classified_batch",
                batch_start=start,
                batch_size=len(batch),
                chunk_ids=[c["id"] for c in batch],
            )

    return outcome


def _classify_batch(router: ModelRouter, prompt_text: str, payload: dict, log) -> list[dict]:
    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": json.dumps(payload)},
    ]
    for attempt in (1, 2):
        try:
            response = router.chat("classifier", messages, json_mode=True)
            parsed = json.loads(response.text)
            results = parsed.get("results")
            if isinstance(results, list):
                return results
        except (ModelCallError, json.JSONDecodeError) as exc:
            if log:
                log.warning("classifier_batch_failed", attempt=attempt, error=str(exc))
    return []  # whole batch falls back to ambiguous -> excluded + flagged
