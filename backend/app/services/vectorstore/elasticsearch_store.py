import logging
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.services.vectorstore.base import SearchHit, VectorRecord

logger = logging.getLogger(__name__)


class ElasticsearchVectorStore:
    def __init__(
        self,
        client: AsyncElasticsearch,
        index_name: str,
        dimensions: int,
    ) -> None:
        self._client = client
        self._index_name = index_name
        self._dimensions = dimensions

    async def ensure_index(self) -> None:
        if await self._client.indices.exists(index=self._index_name):
            return

        await self._client.indices.create(
            index=self._index_name,
            mappings={
                "properties": {
                    "document_id": {"type": "keyword"},
                    "workspace_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "content": {"type": "text"},
                    "page_number": {"type": "integer"},
                    "metadata": {"type": "object", "enabled": True},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": self._dimensions,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        )

    async def index_chunks(
        self,
        records: list[VectorRecord],
    ) -> None:
        if not records:
            return

        await self.ensure_index()

        actions = [
            {
                "_op_type": "index",
                "_index": self._index_name,
                "_id": record.id,
                "_source": {
                    "document_id": record.document_id,
                    "workspace_id": record.workspace_id,
                    "chunk_index": record.chunk_index,
                    "content": record.content,
                    "page_number": record.page_number,
                    "metadata": record.metadata,
                    "embedding": record.embedding,
                },
            }
            for record in records
        ]

        await async_bulk(self._client, actions)

    async def delete_by_document(self, document_id: str) -> None:
        await self._client.delete_by_query(
            index=self._index_name,
            query={"term": {"document_id": document_id}},
            ignore_unavailable=True,
            conflicts="proceed",
        )

    async def vector_search(
        self,
        *,
        embedding: list[float],
        workspace_id: str,
        top_k: int,
    ) -> list[SearchHit]:
        if not await self._client.indices.exists(index=self._index_name):
            return []

        response = await self._client.search(
            index=self._index_name,
            knn={
                "field": "embedding",
                "query_vector": embedding,
                "k": top_k,
                "num_candidates": max(top_k * 10, 50),
                "filter": {"term": {"workspace_id": workspace_id}},
            },
            size=top_k,
            source_excludes=["embedding"],
        )

        return self._to_hits(response)

    async def bm25_search(
        self,
        *,
        query: str,
        workspace_id: str,
        top_k: int,
    ) -> list[SearchHit]:
        if not await self._client.indices.exists(index=self._index_name):
            return []

        response = await self._client.search(
            index=self._index_name,
            query={
                "bool": {
                    "must": {"match": {"content": query}},
                    "filter": {"term": {"workspace_id": workspace_id}},
                }
            },
            size=top_k,
            source_excludes=["embedding"],
        )

        return self._to_hits(response)

    @staticmethod
    def _to_hits(response: Any) -> list[SearchHit]:
        return [
            SearchHit(
                id=hit["_id"],
                document_id=hit["_source"]["document_id"],
                workspace_id=hit["_source"]["workspace_id"],
                chunk_index=hit["_source"]["chunk_index"],
                content=hit["_source"]["content"],
                page_number=hit["_source"].get("page_number"),
                score=hit["_score"] or 0.0,
                metadata=hit["_source"].get("metadata") or {},
            )
            for hit in response["hits"]["hits"]
        ]

    async def close(self) -> None:
        await self._client.close()
