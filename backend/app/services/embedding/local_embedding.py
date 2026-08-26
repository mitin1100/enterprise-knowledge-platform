import hashlib
import math
import random

from app.services.embedding.base import EmbeddingService


class LocalHashEmbeddingService(EmbeddingService):
    """
    Deterministic, dependency-free embedding for local development and
    tests. Vectors are not semantically meaningful — only useful to
    exercise the chunking/storage pipeline without a Google API key.
    """

    model_name = "local-hash-embedding"

    def __init__(self, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        seed = int.from_bytes(
            hashlib.sha256(text.encode("utf-8")).digest()[:8],
            byteorder="big",
        )
        generator = random.Random(seed)

        vector = [
            generator.uniform(-1.0, 1.0)
            for _ in range(self.dimensions)
        ]

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0

        return [value / norm for value in vector]
