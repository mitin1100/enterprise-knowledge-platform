import csv
import io
import json

from app.schemas.evaluation import EvaluationDatasetItem
from app.services.evaluation.exception import InvalidDatasetError

# Multiple sources in a single CSV cell are pipe-separated, since commas
# and semicolons both collide with common CSV dialects/locales.
_CSV_SOURCE_SEPARATOR = "|"


def parse_dataset_file(filename: str, content: bytes) -> list[EvaluationDatasetItem]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidDatasetError(
            "Dataset file must be UTF-8 encoded text."
        ) from exc

    if filename.lower().endswith(".csv"):
        return _parse_csv(text)

    return _parse_json(text)


def _parse_json(text: str) -> list[EvaluationDatasetItem]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidDatasetError(f"Invalid JSON dataset: {exc}") from exc

    if not isinstance(payload, list):
        raise InvalidDatasetError(
            "JSON dataset must be a list of {question, expected_answer, "
            "expected_source} objects."
        )

    items = []

    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise InvalidDatasetError(
                f"Dataset row {index} must be an object."
            )

        items.append(_build_item(index, row.get("expected_source"), row))

    return items


def _parse_csv(text: str) -> list[EvaluationDatasetItem]:
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None or "question" not in reader.fieldnames:
        raise InvalidDatasetError(
            "CSV dataset must have a 'question' column (and optionally "
            "'expected_answer', 'expected_source')."
        )

    items = []

    for index, row in enumerate(reader):
        raw_sources = row.get("expected_source") or ""
        sources = [
            source.strip()
            for source in raw_sources.split(_CSV_SOURCE_SEPARATOR)
            if source.strip()
        ]

        items.append(_build_item(index, sources, row))

    return items


def _build_item(
    index: int,
    expected_source: object,
    row: dict,
) -> EvaluationDatasetItem:
    question = str(row.get("question") or "").strip()

    if not question:
        raise InvalidDatasetError(f"Dataset row {index} is missing 'question'.")

    if expected_source is None:
        sources: list[str] = []
    elif isinstance(expected_source, list):
        sources = [str(source).strip() for source in expected_source if str(source).strip()]
    else:
        sources = [str(expected_source).strip()] if str(expected_source).strip() else []

    try:
        return EvaluationDatasetItem(
            question=question,
            expected_answer=str(row.get("expected_answer") or "").strip(),
            expected_source=sources,
        )
    except Exception as exc:
        raise InvalidDatasetError(f"Dataset row {index} is invalid: {exc}") from exc
