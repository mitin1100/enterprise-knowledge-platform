from abc import ABC, abstractmethod
from typing import BinaryIO

from pathlib import Path


class StorageService(ABC):
    @abstractmethod
    async def upload(
        self,
        file_object: BinaryIO,
        storage_key: str,
        content_type: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def download(
        self,
        storage_key: str,
    ) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        storage_key: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def exists(
        self,
        storage_key: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def download_file(
        self,
        storage_key: str,
        destination: Path,
    ) -> None:
        raise NotImplementedError
