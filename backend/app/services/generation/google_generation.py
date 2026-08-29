import asyncio
import logging

from google import genai
from google.genai import types

from app.schemas.retrieval import RetrievedChunk
from app.services.generation.base import GeneratedAnswer, GenerationService
from app.services.generation.exception import GenerationError
from app.services.generation.prompt import build_prompt, parse_response

logger = logging.getLogger(__name__)


class GoogleGenerationService(GenerationService):
    """
    Cloud generation via Gemini, used as the primary/default LLM
    provider for answering questions over retrieved context.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._client = genai.Client(api_key=api_key)

    async def generate_answer(
        self,
        query: str,
        context: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        prompt = build_prompt(query, context)

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self._temperature,
                    max_output_tokens=self._max_output_tokens,
                ),
            )
        except Exception as exc:
            logger.exception("Google generation call failed.")
            raise GenerationError(
                "Failed to generate an answer using the Google LLM."
            ) from exc

        return parse_response(response.text or "", len(context))
