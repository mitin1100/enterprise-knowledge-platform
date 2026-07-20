import asyncio

from app.core.config import get_settings
from app.services.storage.base import StorageService
from app.services.storage.local_storage import LocalStorageService
from app.services.storage.minio_storage import MinioStorageService


async def get_storage_service() -> StorageService:
    settings = get_settings()

    if settings.STORAGE_PROVIDER == "local":
        return LocalStorageService(
            base_path=settings.LOCAL_STORAGE_PATH,
        )

    if settings.STORAGE_PROVIDER == "minio":
        return await asyncio.to_thread(
            MinioStorageService,
            settings.MINIO_ENDPOINT,
            (
                settings.MINIO_ACCESS_KEY.get_secret_value()
                if settings.MINIO_ACCESS_KEY
                else ""
            ),
            (
                settings.MINIO_SECRET_KEY.get_secret_value()
                if settings.MINIO_SECRET_KEY
                else ""
            ),
            settings.MINIO_BUCKET_NAME,
        )

    raise ValueError(
        f"Unsupported storage provider: {settings.STORAGE_PROVIDER}"
    )
