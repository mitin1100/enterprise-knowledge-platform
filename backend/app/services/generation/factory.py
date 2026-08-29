from app.core.config import get_settings
from app.services.generation.base import GenerationService


def get_generation_service() -> GenerationService:
    settings = get_settings()

    if settings.generation_provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY must be configured when "
                "GENERATION_PROVIDER=google."
            )

        from app.services.generation.google_generation import (
            GoogleGenerationService,
        )

        return GoogleGenerationService(
            api_key=settings.GOOGLE_API_KEY.get_secret_value(),
            model=settings.generation_model,
            temperature=settings.generation_temperature,
            max_output_tokens=settings.generation_max_output_tokens,
        )

    if settings.generation_provider == "ollama":
        from app.services.generation.ollama_generation import (
            OllamaGenerationService,
        )

        return OllamaGenerationService(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.generation_model,
            temperature=settings.generation_temperature,
            max_output_tokens=settings.generation_max_output_tokens,
        )

    raise ValueError(
        f"Unsupported generation provider: {settings.generation_provider}"
    )
