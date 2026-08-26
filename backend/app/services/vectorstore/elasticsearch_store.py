import logging

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.services.vectorstore.base import VectorRecord

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

    async def close(self) -> None:
        await self._client.close()
