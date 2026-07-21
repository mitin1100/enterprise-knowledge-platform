import asyncio
from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO
import shutil

from app.services.storage.base import StorageService


class LocalStorageService(StorageService):
    def __init__(self, base_path: Path):
        self.base_path = base_path.resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

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
        )

    def _upload_sync(
        self,
        file_object: BinaryIO,
        storage_key: str,
    ) -> None:
        target_path = self._resolve_path(storage_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        file_object.seek(0)

        with target_path.open("wb") as output_file:
            copyfileobj(file_object, output_file)

        file_object.seek(0)

    async def download(
        self,
        storage_key: str,
    ) -> bytes:
        return await asyncio.to_thread(
            self._resolve_path(storage_key).read_bytes
        )

    async def delete(
        self,
        storage_key: str,
    ) -> None:
        await asyncio.to_thread(self._delete_sync, storage_key)

    def _delete_sync(
        self,
        storage_key: str,
    ) -> None:
        target_path = self._resolve_path(storage_key)

        if target_path.exists():
            target_path.unlink()

    async def exists(
        self,
        storage_key: str,
    ) -> bool:
        return await asyncio.to_thread(
            self._resolve_path(storage_key).exists
        )

    def _resolve_path(
        self,
        storage_key: str,
    ) -> Path:
        target_path = (self.base_path / storage_key).resolve()

        if self.base_path not in target_path.parents:
            raise ValueError("Invalid storage path")

        return target_path

    async def download_file(
        self,
        storage_key: str,
        destination: Path,
    ) -> None:
        source = (
            self.base_path / storage_key
        ).resolve()

        if self.base_path not in source.parents:
            raise ValueError("Invalid storage key.")

        if not source.is_file():
            raise FileNotFoundError(
                f"Storage object does not exist: {storage_key}"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        await asyncio.to_thread(
            shutil.copyfile,
            source,
            destination,
        )
