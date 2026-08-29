import asyncio
import logging
from time import perf_counter
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.evaluation import EvaluationItem, EvaluationRun
from app.repositories.document import DocumentRepository
from app.repositories.evaluation import EvaluationRepository
from app.schemas.evaluation import (
    EvaluationDatasetItem,
    EvaluationItemResult,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationRunSummary,
    LatencyResult,
    RetrievedChunkResult,
    TokenUsageResult,
)
from app.schemas.retrieval import RetrievalLevel, RetrievedChunk
from app.services.chunking.tokenizer import Tokenizer
from app.services.citation.service import make_preview
from app.services.embedding.base import EmbeddingService
from app.services.evaluation import metrics
from app.services.evaluation.exception import EmptyDatasetError
from app.services.evaluation.judge import (
    build_faithfulness_prompt,
    parse_faithfulness_response,
)
from app.services.generation.base import GeneratedAnswer, GenerationService
from app.services.generation.exception import GenerationError
from app.services.generation.prompt import build_prompt
from app.services.retrieval.exception import EmptyQueryError
from app.services.retrieval.service import RetrievalService

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Runs an evaluation dataset end-to-end through the RAG pipeline
    (retrieve -> generate) and scores each answer on retrieval
    precision, context relevance, answer faithfulness, answer
    relevancy, hallucination, latency and token usage, then persists
    the run for the evaluation dashboard.
    """

    def __init__(
        self,
        session: AsyncSession,
        retrieval_service: RetrievalService,
        generation_service: GenerationService,
        embedding_service: EmbeddingService,
    ) -> None:
        self._session = session
        self._retrieval_service = retrieval_service
        self._generation_service = generation_service
        self._embedding_service = embedding_service
        self._document_repository = DocumentRepository(session)
        self._evaluation_repository = EvaluationRepository(session)
        self._tokenizer = Tokenizer(settings.chunking_token_encoding)

    async def run_evaluation(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        payload: EvaluationRunRequest,
    ) -> EvaluationRunResponse:
        if not payload.items:
            raise EmptyDatasetError("Evaluation dataset must not be empty.")

        top_k = payload.top_k or settings.generation_context_chunk_limit
        pass_threshold = (
            payload.pass_threshold
            if payload.pass_threshold is not None
            else settings.evaluation_pass_threshold
        )

        results = [
            await self._evaluate_item(
                workspace_id=workspace_id,
                item=item,
                level=payload.retrieval_level,
                top_k=top_k,
                pass_threshold=pass_threshold,
            )
            for item in payload.items
        ]

        run = await self._persist_run(
            workspace_id=workspace_id,
            user_id=user_id,
            name=payload.name,
            retrieval_level=int(payload.retrieval_level),
            pass_threshold=pass_threshold,
            results=results,
        )

        await self._session.commit()

        return self.to_run_response(run)

    async def _evaluate_item(
        self,
        *,
        workspace_id: UUID,
        item: EvaluationDatasetItem,
        level: RetrievalLevel,
        top_k: int,
        pass_threshold: float,
    ) -> dict:
        question = item.question.strip()
        t0 = perf_counter()

        try:
            retrieval = await self._retrieval_service.retrieve(
                query=question,
                workspace_id=str(workspace_id),
                level=level,
                top_k=top_k,
            )
        except EmptyQueryError as exc:
            return self._error_item(item, f"Retrieval failed: {exc}")

        t1 = perf_counter()
        context = retrieval.results[: settings.generation_context_chunk_limit]

        try:
            generated = await self._generation_service.generate_answer(
                query=question,
                context=context,
                history=None,
            )
        except GenerationError as exc:
            return self._error_item(item, f"Generation failed: {exc}")

        t2 = perf_counter()

        document_names = await self._document_names(context)

        retrieval_precision = metrics.retrieval_precision(
            context, item.expected_source, document_names
        )
        context_relevance, answer_relevancy = await self._embedding_metrics(
            question, generated.answer, context
        )
        faithfulness, judge_reasoning = await self._judge_faithfulness(
            question, generated.answer, item.expected_answer, context
        )
        hallucinated = faithfulness < settings.evaluation_hallucination_threshold

        prompt_tokens, completion_tokens, tokens_estimated = self._token_usage(
            generated, question, context
        )

        scored_components = [
            value
            for value in (
                retrieval_precision,
                context_relevance,
                faithfulness,
                answer_relevancy,
            )
            if value is not None
        ]
        score = metrics.mean(scored_components)
        passed = score >= pass_threshold and not hallucinated

        return {
            "question": question,
            "expected_answer": item.expected_answer,
            "expected_source": item.expected_source,
            "generated_answer": generated.answer,
            "retrieved_chunks": [
                self._chunk_to_dict(chunk, document_names) for chunk in context
            ],
            "retrieval_precision": retrieval_precision,
            "context_relevance": context_relevance,
            "answer_faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "hallucinated": hallucinated,
            "judge_reasoning": judge_reasoning,
            "retrieval_latency_ms": (t1 - t0) * 1000,
            "generation_latency_ms": (t2 - t1) * 1000,
            "total_latency_ms": (t2 - t0) * 1000,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "tokens_estimated": tokens_estimated,
            "score": score,
            "passed": passed,
            "error_message": None,
        }

    async def _document_names(
        self,
        context: list[RetrievedChunk],
    ) -> dict[str, str]:
        if not context:
            return {}

        document_ids = {UUID(chunk.document_id) for chunk in context}
        documents = await asyncio.gather(
            *(
                self._document_repository.get_by_id(document_id)
                for document_id in document_ids
            )
        )

        return {
            str(document.id): document.original_filename
            for document in documents
            if document is not None
        }

    async def _embedding_metrics(
        self,
        question: str,
        answer: str,
        context: list[RetrievedChunk],
    ) -> tuple[float, float]:
        question_embedding = await self._embedding_service.embed_query(question)
        document_embeddings = await self._embedding_service.embed_texts(
            [answer] + [chunk.content for chunk in context]
        )
        answer_embedding = document_embeddings[0]
        chunk_embeddings = document_embeddings[1:]

        context_relevance = metrics.mean(
            [
                metrics.cosine_similarity(question_embedding, chunk_embedding)
                for chunk_embedding in chunk_embeddings
            ]
        )
        answer_relevancy = metrics.cosine_similarity(
            question_embedding, answer_embedding
        )

        return context_relevance, answer_relevancy

    async def _judge_faithfulness(
        self,
        question: str,
        answer: str,
        expected_answer: str,
        context: list[RetrievedChunk],
    ) -> tuple[float, str]:
        prompt = build_faithfulness_prompt(question, answer, expected_answer, context)

        try:
            raw = await self._generation_service.generate_judgment(prompt)
        except GenerationError:
            logger.warning("Faithfulness judge call failed; defaulting to 0.0.")
            return 0.0, "Judge call failed."

        return parse_faithfulness_response(raw)

    def _token_usage(
        self,
        generated: GeneratedAnswer,
        question: str,
        context: list[RetrievedChunk],
    ) -> tuple[int, int, bool]:
        if generated.usage is not None:
            return (
                generated.usage.prompt_tokens,
                generated.usage.completion_tokens,
                False,
            )

        prompt_text = build_prompt(question, context, None)

        return (
            self._tokenizer.count_tokens(prompt_text),
            self._tokenizer.count_tokens(generated.answer),
            True,
        )

    @staticmethod
    def _chunk_to_dict(
        chunk: RetrievedChunk,
        document_names: dict[str, str],
    ) -> dict:
        return {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "document_name": document_names.get(chunk.document_id),
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "content_preview": make_preview(chunk.content),
            "score": chunk.score,
        }

    @staticmethod
    def _error_item(item: EvaluationDatasetItem, error: str) -> dict:
        return {
            "question": item.question.strip(),
            "expected_answer": item.expected_answer,
            "expected_source": item.expected_source,
            "generated_answer": "",
            "retrieved_chunks": [],
            "retrieval_precision": None,
            "context_relevance": 0.0,
            "answer_faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "hallucinated": False,
            "judge_reasoning": None,
            "retrieval_latency_ms": 0.0,
            "generation_latency_ms": 0.0,
            "total_latency_ms": 0.0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "tokens_estimated": True,
            "score": 0.0,
            "passed": False,
            "error_message": error,
        }

    async def _persist_run(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        name: str | None,
        retrieval_level: int,
        pass_threshold: float,
        results: list[dict],
    ) -> EvaluationRun:
        successful = [result for result in results if result["error_message"] is None]
        precisions = [
            result["retrieval_precision"]
            for result in successful
            if result["retrieval_precision"] is not None
        ]

        return await self._evaluation_repository.create_run(
            workspace_id=workspace_id,
            created_by=user_id,
            name=name,
            retrieval_level=retrieval_level,
            pass_threshold=pass_threshold,
            item_count=len(results),
            passed_count=sum(1 for result in results if result["passed"]),
            avg_retrieval_precision=(
                metrics.mean(precisions) if precisions else None
            ),
            avg_context_relevance=metrics.mean(
                [result["context_relevance"] for result in successful]
            ),
            avg_answer_faithfulness=metrics.mean(
                [result["answer_faithfulness"] for result in successful]
            ),
            avg_answer_relevancy=metrics.mean(
                [result["answer_relevancy"] for result in successful]
            ),
            hallucination_rate=(
                sum(1 for result in successful if result["hallucinated"])
                / len(successful)
                if successful
                else 0.0
            ),
            avg_latency_ms=metrics.mean(
                [result["total_latency_ms"] for result in successful]
            ),
            total_prompt_tokens=sum(result["prompt_tokens"] for result in results),
            total_completion_tokens=sum(
                result["completion_tokens"] for result in results
            ),
            total_tokens=sum(
                result["prompt_tokens"] + result["completion_tokens"]
                for result in results
            ),
            items=results,
        )

    @staticmethod
    def to_item_result(item: EvaluationItem) -> EvaluationItemResult:
        return EvaluationItemResult(
            id=item.id,
            question=item.question,
            expected_answer=item.expected_answer,
            expected_source=item.expected_source,
            generated_answer=item.generated_answer,
            retrieved_chunks=[
                RetrievedChunkResult(**chunk) for chunk in item.retrieved_chunks
            ],
            retrieval_precision=item.retrieval_precision,
            context_relevance=item.context_relevance,
            answer_faithfulness=item.answer_faithfulness,
            answer_relevancy=item.answer_relevancy,
            hallucinated=item.hallucinated,
            judge_reasoning=item.judge_reasoning,
            latency=LatencyResult(
                retrieval_ms=item.retrieval_latency_ms,
                generation_ms=item.generation_latency_ms,
                total_ms=item.total_latency_ms,
            ),
            token_usage=TokenUsageResult(
                prompt_tokens=item.prompt_tokens,
                completion_tokens=item.completion_tokens,
                total_tokens=item.prompt_tokens + item.completion_tokens,
                estimated=item.tokens_estimated,
            ),
            score=item.score,
            passed=item.passed,
            error=item.error_message,
        )

    @classmethod
    def to_run_response(cls, run: EvaluationRun) -> EvaluationRunResponse:
        summary = EvaluationRunSummary.model_validate(run)

        return EvaluationRunResponse(
            **summary.model_dump(),
            items=[cls.to_item_result(item) for item in run.items],
        )
