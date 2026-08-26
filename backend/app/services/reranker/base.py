from abc import ABC, abstractmethod

from app.schemas.retrieval import RetrievedChunk


class RerankerService(ABC):
    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """
        Reorder candidates by relevance to the query and return the top_k,
        with rerank_score populated on each returned chunk.
        """
        raise NotImplementedError
