"""Topic grouping and section writing (FR-010/FR-011/FR-014).

Stories are generated only from retrieved eligible chunks; every statement carries
citation markers which are validated by :mod:`newsletter_engine.generation.citations`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from newsletter_engine.generation import citations
from newsletter_engine.models.provider import ModelCallError
from newsletter_engine.models.router import ModelRouter
from newsletter_engine.retrieval.index import ChunkIndex

_MAX_TOPICS = 8
_MAX_STORY_CHUNKS = 40
_SNIPPET_CHARS = 200
_CHUNK_CHARS = 2000

_TOPIC_PROMPT = """\
You group engineering meeting content into newsletter topics. You receive chunks, each
with a short numeric id and a text snippet. Produce 3-8 focused, coherent technical
topics, each a distinct theme (a specific architecture, tool, practice, or decision).
Assign a chunk to at most one topic; ignore chunks that fit nowhere. Prefer several
tight topics over one broad one. Reference chunks only by the numeric ids given.
Respond with JSON only:
{"topics": [{"title": "Topic title", "chunk_ids": [0, 4, 7]}]}
"""

_ACTION_ITEMS_PROMPT = """\
You extract action items from engineering meeting content for a newsletter. You receive
source chunks. List concrete follow-ups as markdown bullets, each starting with the
owning role in bold (e.g. "- **Solution Architect**: ..."). Use roles, never personal
names. Only include action items actually present in the chunks; if there are none,
return an empty string. Respond with JSON only: {"body_md": "- ..."}
"""


@dataclass
class Topic:
    title: str
    chunk_ids: list[str]


@dataclass
class StoryDraft:
    topic_title: str
    title: str = ""
    body_md: str = ""
    citations: list[citations.ExtractedCitation] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    insufficient_support: bool = False


def group_topics(chunks: list[dict], *, router: ModelRouter, log=None) -> list[Topic]:
    eligible = [c for c in chunks if c.get("eligible")]
    if not eligible:
        return []
    # Address chunks by short numeric index in the grouping call: making the model echo
    # back full chunk UUIDs (one per chunk) overflows the response token budget at scale
    # and truncates the JSON, collapsing every run to the catch-all topic below.
    index_to_id = {str(n): c["id"] for n, c in enumerate(eligible)}
    payload = {
        "chunks": [
            {"id": str(n), "snippet": c["text"][:_SNIPPET_CHARS]}
            for n, c in enumerate(eligible)
        ]
    }
    try:
        response = router.chat(
            "writer",
            [
                {"role": "system", "content": _TOPIC_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            json_mode=True,
        )
        raw_topics = json.loads(response.text).get("topics", [])
    except (ModelCallError, json.JSONDecodeError) as exc:
        if log:
            log.warning("topic_grouping_failed", error=str(exc))
        raw_topics = []

    topics = []
    for raw in raw_topics[:_MAX_TOPICS]:
        ids = [index_to_id[str(i)] for i in raw.get("chunk_ids", []) if str(i) in index_to_id]
        if raw.get("title") and ids:
            topics.append(Topic(title=raw["title"], chunk_ids=ids))

    if not topics:  # fallback: one catch-all topic so the run still produces a draft
        topics = [Topic(title="This Month in Engineering", chunk_ids=[c["id"] for c in eligible])]
    if log:
        log.info("topics_grouped", count=len(topics), titles=[t.title for t in topics])
    return topics


def write_story(
    topic: Topic,
    *,
    edition_id: str,
    chunk_lookup: dict[str, dict],
    index: ChunkIndex,
    router: ModelRouter,
    prompt_text: str,
    log=None,
) -> StoryDraft:
    draft = StoryDraft(topic_title=topic.title)

    # Retrieval-augmented selection: take the chunks most relevant to the topic title
    # first (a large topic otherwise fills the cap with its arbitrary head, burying the
    # coherent core), then top up with remaining topic members.
    selected: list[str] = []
    seen: set[str] = set()
    for chunk_id, _distance in index.query(edition_id, topic.title, k=_MAX_STORY_CHUNKS):
        if chunk_id in chunk_lookup and chunk_id not in seen:
            selected.append(chunk_id)
            seen.add(chunk_id)
    for chunk_id in topic.chunk_ids:
        if chunk_id in chunk_lookup and chunk_id not in seen:
            selected.append(chunk_id)
            seen.add(chunk_id)
    selected = selected[:_MAX_STORY_CHUNKS]
    if not selected:
        draft.insufficient_support = True
        draft.flags.append("insufficient_support")
        return draft

    # Address chunks by short id in the prompt: handed full UUIDs, models abbreviate them
    # in citation markers (e.g. [C:db8440a8]), which then fail validation. We expand the
    # short markers back to full chunk ids before extraction so the rest of the pipeline
    # keeps working with real ids.
    short_to_id = {str(n): cid for n, cid in enumerate(selected)}
    payload = {
        "topic": topic.title,
        "chunks": [
            {"id": str(n), "text": chunk_lookup[cid]["text"][:_CHUNK_CHARS]}
            for n, cid in enumerate(selected)
        ],
    }
    try:
        response = router.chat(
            "writer",
            [
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": json.dumps(payload)},
            ],
            json_mode=True,
        )
        parsed = json.loads(response.text)
    except (ModelCallError, json.JSONDecodeError) as exc:
        if log:
            log.warning("story_write_failed", topic=topic.title, error=str(exc))
        draft.insufficient_support = True
        draft.flags.append("insufficient_support")
        return draft

    if parsed.get("insufficient_support") or not parsed.get("body_md"):
        draft.insufficient_support = True
        draft.flags.append("insufficient_support")
        return draft

    body_md = citations.expand_short_markers(parsed["body_md"], short_to_id)
    extraction = citations.extract(body_md, set(selected))
    draft.title = parsed.get("title") or topic.title
    draft.body_md = extraction.body_md
    draft.citations = extraction.citations
    if extraction.invalid_ids:
        draft.flags.append("invalid_citations_dropped")
        if log:
            log.warning(
                "invalid_citations_dropped",
                topic=topic.title,
                invalid_ids=extraction.invalid_ids,
            )
    if extraction.insufficient_support:
        # No statement survived citation validation -> omit at the orchestrator (FR-014)
        draft.insufficient_support = True
        draft.flags.append("insufficient_support")
    return draft


def write_tldr(stories: list[StoryDraft], *, router: ModelRouter, prompt_text: str, log=None) -> str:
    payload = {
        "stories": [{"title": s.title, "body_md": s.body_md} for s in stories]
    }
    try:
        response = router.chat(
            "writer",
            [
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": json.dumps(payload)},
            ],
            json_mode=True,
        )
        return json.loads(response.text).get("body_md", "")
    except (ModelCallError, json.JSONDecodeError) as exc:
        if log:
            log.warning("tldr_failed", error=str(exc))
        return ""


def write_action_items(
    chunks: list[dict], *, router: ModelRouter, log=None, max_chunks: int = 30
) -> str:
    eligible = [c for c in chunks if c.get("eligible")][:max_chunks]
    if not eligible:
        return ""
    payload = {
        "chunks": [{"id": c["id"], "text": c["text"][:_CHUNK_CHARS]} for c in eligible]
    }
    try:
        response = router.chat(
            "writer",
            [
                {"role": "system", "content": _ACTION_ITEMS_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            json_mode=True,
        )
        return json.loads(response.text).get("body_md", "")
    except (ModelCallError, json.JSONDecodeError) as exc:
        if log:
            log.warning("action_items_failed", error=str(exc))
        return ""
