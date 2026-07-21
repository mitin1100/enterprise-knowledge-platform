import asyncio
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error
from pathlib import Path

from app.services.storage.base import StorageService


class MinioStorageService(StorageService):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,

    ):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.bucket_name = bucket_name

        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    async def upload(
        self,
        file_object: BinaryIO,
        storage_key: str,
        content_type: str,
    ) -> None:
        await asyncio.to_thread(
            self._upload_sync,
            file_object,
            storage_key,
            content_type,
        )

    def _upload_sync(
        self,
        file_object: BinaryIO,
        storage_key: str,
        content_type: str,
    ) -> None:
        file_object.seek(0, 2)
        file_size = file_object.tell()
        file_object.seek(0)

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=storage_key,
            data=file_object,
            length=file_size,
            content_type=content_type,
        )

        file_object.seek(0)

    async def download(
        self,
        storage_key: str,
    ) -> bytes:
        return await asyncio.to_thread(
            self._download_sync,
            storage_key,
        )

    def _download_sync(
        self,
        storage_key: str,
    ) -> bytes:
        response = self.client.get_object(
            self.bucket_name,
            storage_key,
        )

        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete(
        self,
        storage_key: str,
    ) -> None:
        await asyncio.to_thread(
            self.client.remove_object,
            self.bucket_name,
            storage_key,
        )

    async def exists(
        self,
        storage_key: str,
    ) -> bool:
        return await asyncio.to_thread(
            self._exists_sync,
            storage_key,
        )

    def _exists_sync(
        self,
        storage_key: str,
    ) -> bool:
        try:
            self.client.stat_object(
                self.bucket_name,
                storage_key,
            )
            return True
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                return False
            raise

    async def download_file(
        self,
        storage_key: str,
        destination: Path,
    ) -> None:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        await asyncio.to_thread(
            self.client.fget_object,
            self.bucket_name,
            storage_key,
            str(destination),
        )
