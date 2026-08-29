import json
import logging

from app.schemas.retrieval import RetrievedChunk
from app.services.generation.base import GeneratedAnswer

logger = logging.getLogger(__name__)

NOT_FOUND_ANSWER = (
    "I could not find this information in the provided documents."
)

_SYSTEM_INSTRUCTIONS = """You are a careful enterprise knowledge-base \
assistant. Answer the user's question using ONLY the numbered sources \
listed below.

Rules:
- Base your answer strictly on the provided sources. Never rely on \
outside knowledge or assumptions beyond what the sources state.
- If the sources do not contain enough information to answer, respond \
with exactly: "{not_found}"
- Do not fabricate facts, numbers, or citations.
- Write a clear, direct answer, in the same language as the question.
- Every factual claim must be traceable to at least one numbered source.

Respond with ONLY a JSON object of this exact shape, and nothing else:
{{"answer": "<your answer text>", "cited_sources": [<source numbers \
you actually relied on, e.g. 1, 3>]}}
""".format(not_found=NOT_FOUND_ANSWER)


def build_prompt(query: str, context: list[RetrievedChunk]) -> str:
    if not context:
        sources = "(no sources retrieved)"
    else:
        sources = "\n\n".join(
            f"[{index}] {chunk.content}"
            for index, chunk in enumerate(context, start=1)
        )

    return (
        f"{_SYSTEM_INSTRUCTIONS}\n\n"
        f"Question: {query}\n\n"
        f"Sources:\n{sources}\n"
    )


def parse_response(raw_text: str, context_len: int) -> GeneratedAnswer:
    try:
        payload = json.loads(_extract_json_object(raw_text))
        answer = str(payload["answer"]).strip()
        cited_indices = sorted(
            {
                int(number) - 1
                for number in (payload.get("cited_sources") or [])
                if isinstance(number, (int, float))
                and 1 <= int(number) <= context_len
            }
        )
    except Exception:
        logger.warning(
            "Could not parse structured generation response; falling "
            "back to raw text."
        )
        answer = raw_text.strip()
        cited_indices = []

    if not answer:
        answer = NOT_FOUND_ANSWER

    return GeneratedAnswer(answer=answer, cited_indices=cited_indices)


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("Response did not contain a JSON object.")

    return text[start : end + 1]
