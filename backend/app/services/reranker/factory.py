from app.core.config import get_settings
from app.services.reranker.base import RerankerService


def get_reranker_service() -> RerankerService:
    settings = get_settings()

    if settings.reranker_provider == "lexical":
        from app.services.reranker.lexical_reranker import (
            LexicalRerankerService,
        )

        return LexicalRerankerService()

    if settings.reranker_provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY must be configured when "
                "RERANKER_PROVIDER=google."
            )

        from app.services.reranker.google_reranker import (
            GoogleRerankerService,
        )

        return GoogleRerankerService(
            api_key=settings.GOOGLE_API_KEY.get_secret_value(),
            model=settings.reranker_model,
        )

    raise ValueError(
        f"Unsupported reranker provider: {settings.reranker_provider}"
    )
