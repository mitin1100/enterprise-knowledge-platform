import re

from app.schemas.retrieval import RetrievedChunk
from app.services.reranker.base import RerankerService

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


class LexicalRerankerService(RerankerService):
    """
    Dependency-free reranker for local development and tests. Scores each
    candidate by query/content term overlap rather than a learned
    cross-encoder — useful to exercise the reranking pipeline without an
    external API key, not a substitute for a real relevance model.
    """

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        query_terms = self._tokenize(query)

        if not query_terms:
            return candidates[:top_k]

        scored = [
            (self._overlap_score(query_terms, candidate.content), candidate)
            for candidate in candidates
        ]

        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            candidate.model_copy(update={"rerank_score": score})
            for score, candidate in scored[:top_k]
        ]

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token.lower() for token in _TOKEN_PATTERN.findall(text)}

    @classmethod
    def _overlap_score(cls, query_terms: set[str], content: str) -> float:
        content_terms = cls._tokenize(content)

        if not content_terms:
            return 0.0

        overlap = query_terms & content_terms

        return len(overlap) / len(query_terms)
