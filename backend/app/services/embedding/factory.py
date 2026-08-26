from app.core.config import get_settings
from app.services.embedding.base import EmbeddingService


def get_embedding_service() -> EmbeddingService:
    settings = get_settings()

    if settings.embedding_provider == "local":
        from app.services.embedding.local_embedding import (
            LocalHashEmbeddingService,
        )

        return LocalHashEmbeddingService(
            dimensions=settings.embedding_dimensions,
        )

    if settings.embedding_provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY must be configured when "
                "EMBEDDING_PROVIDER=google."
            )

        from app.services.embedding.google_embedding import (
            GoogleEmbeddingService,
        )

        return GoogleEmbeddingService(
            api_key=settings.GOOGLE_API_KEY.get_secret_value(),
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            batch_size=settings.embedding_batch_size,
        )

    raise ValueError(
        f"Unsupported embedding provider: {settings.embedding_provider}"
    )
