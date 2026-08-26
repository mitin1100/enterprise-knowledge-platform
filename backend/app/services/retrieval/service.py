import asyncio
import logging

from app.schemas.retrieval import (
    RetrievalLevel,
    RetrievalResponse,
    RetrievedChunk,
)
from app.services.embedding.base import EmbeddingService
from app.services.reranker.base import RerankerService
from app.services.retrieval.exception import EmptyQueryError
from app.services.vectorstore.base import SearchHit
from app.services.vectorstore.elasticsearch_store import (
    ElasticsearchVectorStore,
)

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Answers "which chunks are most relevant to this question" at three
    increasing levels of sophistication:

    - VECTOR_ONLY: embed the query, kNN search on the embedding field.
    - HYBRID: vector search + BM25 search, merged with Reciprocal Rank
      Fusion (RRF is computed client-side rather than via Elasticsearch's
      `rank.rrf` retriever so this works regardless of ES license tier).
    - HYBRID_RERANKED: HYBRID over a larger candidate pool, then reranked
      down to top_k by the configured reranker service.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: ElasticsearchVectorStore,
        reranker_service: RerankerService,
        *,
        candidate_k: int,
        rrf_k: int,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._reranker_service = reranker_service
        self._candidate_k = candidate_k
        self._rrf_k = rrf_k

    async def retrieve(
        self,
        *,
        query: str,
        workspace_id: str,
        level: RetrievalLevel,
        top_k: int,
    ) -> RetrievalResponse:
        query = query.strip()

        if not query:
            raise EmptyQueryError("Search query must not be empty.")

        if level == RetrievalLevel.VECTOR_ONLY:
            results = await self._vector_only(query, workspace_id, top_k)
        else:
            results = await self._hybrid(
                query,
                workspace_id,
                candidate_k=max(self._candidate_k, top_k),
            )

            if level == RetrievalLevel.HYBRID_RERANKED:
                results = await self._reranker_service.rerank(
                    query,
                    results,
                    top_k,
                )
            else:
                results = results[:top_k]

        return RetrievalResponse(query=query, level=level, results=results)

    async def _vector_only(
        self,
        query: str,
        workspace_id: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        query_embedding = await self._embedding_service.embed_query(query)

        hits = await self._vector_store.vector_search(
            embedding=query_embedding,
            workspace_id=workspace_id,
            top_k=top_k,
        )

        return [self._to_chunk(hit, vector_score=hit.score) for hit in hits]

    async def _hybrid(
        self,
        query: str,
        workspace_id: str,
        candidate_k: int,
    ) -> list[RetrievedChunk]:
        query_embedding = await self._embedding_service.embed_query(query)

        vector_hits, bm25_hits = await asyncio.gather(
            self._vector_store.vector_search(
                embedding=query_embedding,
                workspace_id=workspace_id,
                top_k=candidate_k,
            ),
            self._vector_store.bm25_search(
                query=query,
                workspace_id=workspace_id,
                top_k=candidate_k,
            ),
        )

        return self._reciprocal_rank_fusion(vector_hits, bm25_hits)

    def _reciprocal_rank_fusion(
        self,
        vector_hits: list[SearchHit],
        bm25_hits: list[SearchHit],
    ) -> list[RetrievedChunk]:
        fused: dict[str, RetrievedChunk] = {}
        rrf_scores: dict[str, float] = {}

        for rank, hit in enumerate(vector_hits, start=1):
            rrf_scores[hit.id] = (
                rrf_scores.get(hit.id, 0.0) + 1.0 / (self._rrf_k + rank)
            )
            fused[hit.id] = self._to_chunk(hit, vector_score=hit.score)

        for rank, hit in enumerate(bm25_hits, start=1):
            rrf_scores[hit.id] = (
                rrf_scores.get(hit.id, 0.0) + 1.0 / (self._rrf_k + rank)
            )

            if hit.id in fused:
                fused[hit.id] = fused[hit.id].model_copy(
                    update={"bm25_score": hit.score}
                )
            else:
                fused[hit.id] = self._to_chunk(hit, bm25_score=hit.score)

        ranked_ids = sorted(
            rrf_scores,
            key=lambda chunk_id: rrf_scores[chunk_id],
            reverse=True,
        )

        return [
            fused[chunk_id].model_copy(
                update={"score": rrf_scores[chunk_id]}
            )
            for chunk_id in ranked_ids
        ]

    @staticmethod
    def _to_chunk(
        hit: SearchHit,
        *,
        vector_score: float | None = None,
        bm25_score: float | None = None,
    ) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=hit.id,
            document_id=hit.document_id,
            chunk_index=hit.chunk_index,
            content=hit.content,
            page_number=hit.page_number,
            score=(
                vector_score if vector_score is not None
                else (bm25_score or 0.0)
            ),
            vector_score=vector_score,
            bm25_score=bm25_score,
            metadata=hit.metadata,
        )
