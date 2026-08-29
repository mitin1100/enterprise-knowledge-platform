from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.schemas.retrieval import RetrievedChunk


@dataclass(slots=True)
class GeneratedAnswer:
    answer: str
    cited_indices: list[int] = field(default_factory=list)


@dataclass(slots=True)
class ChatTurn:
    """A single prior turn used as short-term conversational memory."""

    role: str
    content: str


class GenerationService(ABC):
    @abstractmethod
    async def generate_answer(
        self,
        query: str,
        context: list[RetrievedChunk],
        history: list[ChatTurn] | None = None,
    ) -> GeneratedAnswer:
        """
        Generate an answer to `query` grounded strictly in `context`.

        `history` is a short window of the most recent prior turns
        (oldest first), used only to resolve conversational context such
        as follow-up questions or pronouns — it is never a source of
        facts.

        `cited_indices` are 0-based positions into `context` that the
        model reports it actually relied on to answer.
        """
        raise NotImplementedError
