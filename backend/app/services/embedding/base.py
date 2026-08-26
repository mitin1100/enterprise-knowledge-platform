from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    model_name: str
    dimensions: int

    @abstractmethod
    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate one embedding vector per input text, preserving order.
        """
        raise NotImplementedError

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding vector for a search query. Providers with an
        asymmetric query/document embedding model should override this;
        the default reuses the document embedding path.
        """
        embeddings = await self.embed_texts([text])

        return embeddings[0]
