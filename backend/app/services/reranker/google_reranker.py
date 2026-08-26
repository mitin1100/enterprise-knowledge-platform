import asyncio
import json
import logging

from google import genai

from app.schemas.retrieval import RetrievedChunk
from app.services.reranker.base import RerankerService
from app.services.reranker.lexical_reranker import LexicalRerankerService

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """You are a relevance judge for a document retrieval \
system. Given a user question and a list of candidate passages, score how \
relevant each passage is to answering the question, from 0 (irrelevant) \
to 10 (directly answers it).

Question: {query}

Passages:
{passages}

Respond with ONLY a JSON array of numbers, one score per passage, in the \
same order as listed, e.g. [8, 2, 5]. Do not include any other text.
"""


class GoogleRerankerService(RerankerService):
    """
    LLM-based reranker: asks a Gemini model to score each candidate's
    relevance to the query directly, which can capture semantic
    relationships that BM25 term overlap and embedding cosine similarity
    miss on their own. Falls back to lexical reranking if the model call
    fails or returns an unusable response.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key)
        self._fallback = LexicalRerankerService()

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not candidates:
            return []

        try:
            scores = await self._score_candidates(query, candidates)
        except Exception:
            logger.exception(
                "Google reranker call failed, falling back to lexical "
                "reranking."
            )
            return await self._fallback.rerank(query, candidates, top_k)

        ranked = sorted(
            zip(scores, candidates),
            key=lambda pair: pair[0],
            reverse=True,
        )

        return [
            candidate.model_copy(update={"rerank_score": score})
            for score, candidate in ranked[:top_k]
        ]

    async def _score_candidates(
        self,
        query: str,
        candidates: list[RetrievedChunk],
    ) -> list[float]:
        passages = "\n".join(
            f"[{index}] {candidate.content}"
            for index, candidate in enumerate(candidates)
        )

        prompt = _PROMPT_TEMPLATE.format(query=query, passages=passages)

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model,
            contents=prompt,
        )

        scores = json.loads(self._extract_json_array(response.text or ""))

        if len(scores) != len(candidates):
            raise ValueError(
                "Reranker returned a different number of scores than "
                "candidates."
            )

        return [float(score) for score in scores]

    @staticmethod
    def _extract_json_array(text: str) -> str:
        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1 or end < start:
            raise ValueError(
                "Reranker response did not contain a JSON array."
            )

        return text[start : end + 1]
