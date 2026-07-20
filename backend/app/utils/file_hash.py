import hashlib
from typing import BinaryIO


def calculate_sha256(
    file_object: BinaryIO,
    chunk_size: int = 1024 * 1024,
) -> str:
    sha256 = hashlib.sha256()

    while chunk := file_object.read(chunk_size):
        sha256.update(chunk)

    file_object.seek(0)

    return sha256.hexdigest()
