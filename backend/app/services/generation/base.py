from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.schemas.retrieval import RetrievedChunk


@dataclass(slots=True)
class GeneratedAnswer:
    answer: str
    cited_indices: list[int] = field(default_factory=list)


class GenerationService(ABC):
    @abstractmethod
    async def generate_answer(
        self,
        query: str,
        context: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        """
        Generate an answer to `query` grounded strictly in `context`.

        `cited_indices` are 0-based positions into `context` that the
        model reports it actually relied on to answer.
        """
        raise NotImplementedError
