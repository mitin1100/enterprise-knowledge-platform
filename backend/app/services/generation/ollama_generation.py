import logging

import httpx

from app.schemas.retrieval import RetrievedChunk
from app.services.generation.base import GeneratedAnswer, GenerationService
from app.services.generation.exception import GenerationError
from app.services.generation.prompt import build_prompt, parse_response

logger = logging.getLogger(__name__)


class OllamaGenerationService(GenerationService):
    """
    Self-hosted generation via a local Ollama server, so the platform
    does not depend exclusively on a paid cloud LLM provider.
    """

    def __init__(
        self,
        base_url: str,
        model: str = "llama3.1",
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._timeout = timeout

    async def generate_answer(
        self,
        query: str,
        context: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        prompt = build_prompt(query, context)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json={
                        "model": self._model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": self._temperature,
                            "num_predict": self._max_output_tokens,
                        },
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Ollama generation call failed.")
            raise GenerationError(
                "Failed to reach the self-hosted Ollama model."
            ) from exc

        raw_text = response.json().get("response", "")

        return parse_response(raw_text, len(context))
