from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.evaluation import EvaluationItem, EvaluationRun


class EvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        *,
        workspace_id: UUID,
        created_by: UUID,
        name: str | None,
        retrieval_level: int,
        pass_threshold: float,
        item_count: int,
        passed_count: int,
        avg_retrieval_precision: float | None,
        avg_context_relevance: float,
        avg_answer_faithfulness: float,
        avg_answer_relevancy: float,
        hallucination_rate: float,
        avg_latency_ms: float,
        total_prompt_tokens: int,
        total_completion_tokens: int,
        total_tokens: int,
        items: list[dict],
    ) -> EvaluationRun:
        run = EvaluationRun(
            workspace_id=workspace_id,
            created_by=created_by,
            name=name,
            retrieval_level=retrieval_level,
            pass_threshold=pass_threshold,
            item_count=item_count,
            passed_count=passed_count,
            avg_retrieval_precision=avg_retrieval_precision,
            avg_context_relevance=avg_context_relevance,
            avg_answer_faithfulness=avg_answer_faithfulness,
            avg_answer_relevancy=avg_answer_relevancy,
            hallucination_rate=hallucination_rate,
            avg_latency_ms=avg_latency_ms,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            items=[EvaluationItem(**item) for item in items],
        )

        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)

        return run

    async def get_by_id_and_workspace(
        self,
        *,
        run_id: UUID,
        workspace_id: UUID,
    ) -> EvaluationRun | None:
        statement = (
            select(EvaluationRun)
            .where(
                EvaluationRun.id == run_id,
                EvaluationRun.workspace_id == workspace_id,
            )
            .options(selectinload(EvaluationRun.items))
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        *,
        workspace_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[EvaluationRun]:
        statement = (
            select(EvaluationRun)
            .where(EvaluationRun.workspace_id == workspace_id)
            .order_by(EvaluationRun.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_by_workspace(self, workspace_id: UUID) -> int:
        statement = select(func.count(EvaluationRun.id)).where(
            EvaluationRun.workspace_id == workspace_id
        )

        result = await self._session.execute(statement)
        return result.scalar_one() or 0
