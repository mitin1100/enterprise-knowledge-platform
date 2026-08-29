import asyncio
import logging

from google import genai
from google.genai import types

from app.schemas.retrieval import RetrievedChunk
from app.services.generation.base import (
    ChatTurn,
    GeneratedAnswer,
    GenerationService,
    TokenUsage,
)
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
        history: list[ChatTurn] | None = None,
    ) -> GeneratedAnswer:
        prompt = build_prompt(query, context, history)

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

        generated = parse_response(response.text or "", len(context))
        generated.usage = _extract_usage(response)

        return generated

    async def generate_judgment(self, prompt: str) -> str:
        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0),
            )
        except Exception as exc:
            logger.exception("Google judgment call failed.")
            raise GenerationError(
                "Failed to run the evaluation judge using the Google LLM."
            ) from exc

        return response.text or ""


def _extract_usage(response) -> TokenUsage | None:
    usage = getattr(response, "usage_metadata", None)

    if usage is None:
        return None

    prompt_tokens = getattr(usage, "prompt_token_count", None)
    completion_tokens = getattr(usage, "candidates_token_count", None)

    if prompt_tokens is None or completion_tokens is None:
        return None

    return TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
