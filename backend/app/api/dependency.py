from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services.storage.base import StorageService
from app.services.storage.factory import get_storage_service
from app.services.vectorstore.elasticsearch_store import (
    ElasticsearchVectorStore,
)
from app.services.vectorstore.factory import get_vector_store as _build_vector_store

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise


async def get_storage() -> StorageService:
    return await get_storage_service()


async def get_vector_store() -> AsyncGenerator[
    ElasticsearchVectorStore, None
]:
    vector_store = _build_vector_store()
    try:
        yield vector_store
    finally:
        await vector_store.close()
