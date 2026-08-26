from elasticsearch import AsyncElasticsearch

from app.core.config import get_settings
from app.services.vectorstore.elasticsearch_store import (
    ElasticsearchVectorStore,
)


def get_vector_store() -> ElasticsearchVectorStore:
    settings = get_settings()

    client = AsyncElasticsearch(hosts=[settings.elasticsearch_url])

    return ElasticsearchVectorStore(
        client=client,
        index_name=settings.elasticsearch_chunks_index,
        dimensions=settings.embedding_dimensions,
    )
