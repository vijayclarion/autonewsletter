"""ChromaDB vector index: embeddings via the adapter layer, technical-only retrieval.

Only chunks flagged ``eligible`` (technical, above threshold) are indexed at all, and
queries additionally filter on edition + eligibility metadata — retrieval can never
surface excluded content (constitution Principles II, VII).
"""

from __future__ import annotations

from pathlib import Path

import chromadb

from newsletter_engine.models.router import ModelRouter

_COLLECTION = "content_chunks"
_EMBED_BATCH = 64


class ChunkIndex:
    def __init__(self, persist_dir: str | Path, router: ModelRouter, *, log=None):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            _COLLECTION, metadata={"hnsw:space": "cosine"}
        )
        self._router = router
        self._log = log

    def reset_edition(self, edition_id: str) -> None:
        """Remove a previous run's vectors so re-runs stay idempotent."""
        self._collection.delete(where={"edition_id": edition_id})

    def add_chunks(self, edition_id: str, chunks: list[dict]) -> int:
        eligible = [c for c in chunks if c.get("eligible")]
        for start in range(0, len(eligible), _EMBED_BATCH):
            batch = eligible[start : start + _EMBED_BATCH]
            result = self._router.embed("embedder", [c["text"] for c in batch])
            self._collection.add(
                ids=[c["id"] for c in batch],
                embeddings=result.vectors,
                documents=[c["text"] for c in batch],
                metadatas=[
                    {
                        "edition_id": edition_id,
                        "source_id": c["source_id"],
                        "eligible": True,
                    }
                    for c in batch
                ],
            )
        if self._log:
            self._log.info(
                "index_built", edition_id=edition_id, indexed=len(eligible),
                chunk_ids=[c["id"] for c in eligible],
            )
        return len(eligible)

    def query(self, edition_id: str, text: str, *, k: int = 8) -> list[tuple[str, float]]:
        """Return ``(chunk_id, distance)`` for the edition's eligible chunks only."""
        result = self._router.embed("embedder", [text])
        hits = self._collection.query(
            query_embeddings=result.vectors,
            n_results=k,
            where={"$and": [{"edition_id": edition_id}, {"eligible": True}]},
        )
        ids = hits.get("ids", [[]])[0]
        distances = hits.get("distances", [[]])[0]
        pairs = list(zip(ids, distances))
        if self._log:
            self._log.info(
                "retrieval_query",
                edition_id=edition_id,
                k=k,
                hit_chunk_ids=ids,
                distances=[round(d, 4) for d in distances],
            )
        return pairs
