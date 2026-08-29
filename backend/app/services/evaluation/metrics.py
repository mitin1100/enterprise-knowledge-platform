import math

from app.schemas.retrieval import RetrievedChunk


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    # Similarity scores can be reported as negative for unrelated
    # embeddings; evaluation metrics are only meaningful in [0, 1].
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def retrieval_precision(
    retrieved: list[RetrievedChunk],
    expected_sources: list[str],
    document_names: dict[str, str],
) -> float | None:
    """
    Fraction of retrieved chunks that come from a document the dataset
    marked as an expected source for the question. `expected_sources`
    entries may be a document id or a (partial, case-insensitive)
    filename. Returns None when the dataset item has no expected
    sources, since precision is not defined without ground truth.
    """
    if not expected_sources:
        return None

    if not retrieved:
        return 0.0

    normalized_expected = [source.strip().lower() for source in expected_sources]

    def is_relevant(chunk: RetrievedChunk) -> bool:
        document_name = document_names.get(chunk.document_id, "").lower()
        document_id = chunk.document_id.lower()

        return any(
            expected == document_id
            or expected in document_name
            or (document_name and document_name in expected)
            for expected in normalized_expected
        )

    relevant_count = sum(1 for chunk in retrieved if is_relevant(chunk))

    return relevant_count / len(retrieved)
