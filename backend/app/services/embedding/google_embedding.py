import asyncio

from google import genai
from google.genai import types

from app.services.embedding.base import EmbeddingService


class GoogleEmbeddingService(EmbeddingService):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimensions: int = 768,
        batch_size: int = 32,
    ) -> None:
        self.model_name = model
        self.dimensions = dimensions
        self._batch_size = batch_size
        self._client = genai.Client(api_key=api_key)

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        embeddings: list[list[float]] = []

        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]

            embeddings.extend(await self._embed_batch(batch))

        return embeddings

    async def _embed_batch(
        self,
        batch: list[str],
    ) -> list[list[float]]:
        response = await asyncio.to_thread(
            self._client.models.embed_content,
            model=self.model_name,
            contents=batch,
            config=types.EmbedContentConfig(
                output_dimensionality=self.dimensions,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )

        return [
            list(embedding.values)
            for embedding in response.embeddings
        ]
