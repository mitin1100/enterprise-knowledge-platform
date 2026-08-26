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
