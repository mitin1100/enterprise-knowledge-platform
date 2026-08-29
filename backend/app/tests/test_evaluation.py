import pytest

from app.schemas.evaluation import EvaluationDatasetItem
from app.schemas.retrieval import RetrievedChunk
from app.services.evaluation import metrics
from app.services.evaluation.dataset import parse_dataset_file
from app.services.evaluation.exception import InvalidDatasetError
from app.services.evaluation.judge import (
    build_faithfulness_prompt,
    parse_faithfulness_response,
)


def _chunk(document_id: str, content: str = "some content") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c1",
        document_id=document_id,
        chunk_index=0,
        content=content,
        page_number=1,
        score=0.9,
    )


class TestCosineSimilarity:
    def test_identical_vectors_score_one(self):
        assert metrics.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self):
        assert metrics.cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors_clamped_to_zero(self):
        assert metrics.cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(0.0)

    def test_empty_vectors_score_zero(self):
        assert metrics.cosine_similarity([], []) == 0.0

    def test_mismatched_lengths_score_zero(self):
        assert metrics.cosine_similarity([1.0], [1.0, 0.0]) == 0.0


class TestMean:
    def test_empty_list_is_zero(self):
        assert metrics.mean([]) == 0.0

    def test_averages_values(self):
        assert metrics.mean([1.0, 0.5, 0.0]) == pytest.approx(0.5)


class TestRetrievalPrecision:
    def test_no_expected_sources_returns_none(self):
        result = metrics.retrieval_precision([_chunk("doc-1")], [], {})
        assert result is None

    def test_no_retrieved_chunks_returns_zero(self):
        result = metrics.retrieval_precision([], ["report.pdf"], {})
        assert result == 0.0

    def test_matches_by_filename_substring(self):
        chunks = [_chunk("doc-1"), _chunk("doc-2")]
        names = {"doc-1": "Annual Report.pdf", "doc-2": "Unrelated.docx"}

        result = metrics.retrieval_precision(chunks, ["annual report"], names)

        assert result == pytest.approx(0.5)

    def test_matches_by_document_id(self):
        chunks = [_chunk("doc-1")]

        result = metrics.retrieval_precision(chunks, ["doc-1"], {})

        assert result == pytest.approx(1.0)

    def test_no_match_scores_zero(self):
        chunks = [_chunk("doc-1")]
        names = {"doc-1": "Unrelated.docx"}

        result = metrics.retrieval_precision(chunks, ["annual report"], names)

        assert result == 0.0


class TestDatasetParsing:
    def test_parses_json_list(self):
        content = (
            b'[{"question": "What is X?", "expected_answer": "X is Y.", '
            b'"expected_source": ["policy.pdf"]}]'
        )

        items = parse_dataset_file("dataset.json", content)

        assert items == [
            EvaluationDatasetItem(
                question="What is X?",
                expected_answer="X is Y.",
                expected_source=["policy.pdf"],
            )
        ]

    def test_json_must_be_a_list(self):
        with pytest.raises(InvalidDatasetError):
            parse_dataset_file("dataset.json", b'{"question": "oops"}')

    def test_invalid_json_raises(self):
        with pytest.raises(InvalidDatasetError):
            parse_dataset_file("dataset.json", b"not json")

    def test_parses_csv_with_pipe_separated_sources(self):
        content = (
            b"question,expected_answer,expected_source\n"
            b'"What is X?","X is Y.","policy.pdf|handbook.pdf"\n'
        )

        items = parse_dataset_file("dataset.csv", content)

        assert len(items) == 1
        assert items[0].question == "What is X?"
        assert items[0].expected_source == ["policy.pdf", "handbook.pdf"]

    def test_csv_without_question_column_raises(self):
        content = b"expected_answer\nX is Y.\n"

        with pytest.raises(InvalidDatasetError):
            parse_dataset_file("dataset.csv", content)

    def test_row_without_question_raises(self):
        with pytest.raises(InvalidDatasetError):
            parse_dataset_file("dataset.json", b'[{"expected_answer": "Y"}]')


class TestFaithfulnessJudge:
    def test_build_prompt_includes_question_answer_and_sources(self):
        prompt = build_faithfulness_prompt(
            "What is X?", "X is Y.", "X is Y.", [_chunk("doc-1", "X is Y per policy.")]
        )

        assert "What is X?" in prompt
        assert "X is Y." in prompt
        assert "X is Y per policy." in prompt

    def test_parses_well_formed_response(self):
        score, reasoning = parse_faithfulness_response(
            '{"faithfulness": 0.8, "reasoning": "Mostly grounded."}'
        )

        assert score == pytest.approx(0.8)
        assert reasoning == "Mostly grounded."

    def test_clamps_out_of_range_scores(self):
        score, _ = parse_faithfulness_response('{"faithfulness": 1.5}')
        assert score == 1.0

    def test_falls_back_to_zero_on_malformed_response(self):
        score, reasoning = parse_faithfulness_response("not json at all")

        assert score == 0.0
        assert reasoning
