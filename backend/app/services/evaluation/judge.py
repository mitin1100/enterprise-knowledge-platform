import json
import logging

from app.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

_JUDGE_INSTRUCTIONS = """You are an impartial evaluator for a RAG (retrieval-augmented \
generation) system. Judge whether the AI ANSWER is faithful to the \
provided SOURCES, i.e. whether its claims are actually supported by \
the sources rather than fabricated or drawn from outside knowledge.

Rules:
- Faithfulness is about grounding in the sources, NOT about whether the
  answer matches the reference answer.
- A correct refusal (the answer says the sources do not contain the
  information) is fully faithful and should score 1.0.
- Score 0.0 if the answer asserts facts that are absent from or
  contradicted by the sources.
- Score between 0 and 1 proportionally to the fraction of the answer's
  claims that are supported by the sources.

Respond with ONLY a JSON object of this exact shape, and nothing else:
{"faithfulness": <number between 0 and 1>, "reasoning": "<one short \
sentence explaining the score>"}
"""


def build_faithfulness_prompt(
    question: str,
    generated_answer: str,
    reference_answer: str,
    context: list[RetrievedChunk],
) -> str:
    if not context:
        sources = "(no sources retrieved)"
    else:
        sources = "\n\n".join(
            f"[{index}] {chunk.content}"
            for index, chunk in enumerate(context, start=1)
        )

    reference_section = (
        f"Reference answer (for context only, not the grading target): "
        f"{reference_answer}\n\n"
        if reference_answer
        else ""
    )

    return (
        f"{_JUDGE_INSTRUCTIONS}\n\n"
        f"Question: {question}\n\n"
        f"{reference_section}"
        f"Sources:\n{sources}\n\n"
        f"AI answer: {generated_answer}\n"
    )


def parse_faithfulness_response(raw_text: str) -> tuple[float, str]:
    try:
        payload = json.loads(_extract_json_object(raw_text))
        score = float(payload["faithfulness"])
        reasoning = str(payload.get("reasoning", "")).strip()
    except Exception:
        logger.warning(
            "Could not parse faithfulness judgment; defaulting to 0.0."
        )
        return 0.0, "Could not parse judge response."

    return max(0.0, min(1.0, score)), reasoning


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("Response did not contain a JSON object.")

    return text[start : end + 1]
