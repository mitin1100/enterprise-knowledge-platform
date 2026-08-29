# Evaluation datasets

An evaluation dataset is a list of question/answer/source rows used to
score the RAG pipeline (Phase 10). Each row has three fields:

| Field             | Required | Meaning                                                                                     |
| ------------------ | -------- | --------------------------------------------------------------------------------------------- |
| `question`        | yes      | The question to ask the chat pipeline.                                                       |
| `expected_answer` | no       | A reference answer, used as extra context for the LLM faithfulness judge.                    |
| `expected_source`  | no       | Document filename(s) (or document IDs) the answer should be grounded in, for retrieval precision. Leave empty for questions that should be refused (no supporting document). |

`sample_dataset.json` and `sample_dataset.csv` are equivalent examples
against a fictional employee handbook / policy workspace — replace the
questions and `expected_source` filenames with documents that actually
exist in the workspace you're evaluating before running them.

CSV files may list multiple expected sources in one cell, pipe-separated
(`Policy_A.pdf|Policy_B.pdf`), since commas already delimit CSV columns.

## Running an evaluation

1. Upload the dataset file for a preview/parse check:
   `POST /api/v1/workspaces/{workspace_id}/evaluations/datasets/parse`
   (multipart file upload) -> returns the parsed `items`.
2. Submit those items as an evaluation run:
   `POST /api/v1/workspaces/{workspace_id}/evaluations/runs`
   with `{"items": [...], "retrieval_level": 3}`.
3. View results:
   - `GET /api/v1/workspaces/{workspace_id}/evaluations/runs` — run history (dashboard summary).
   - `GET /api/v1/workspaces/{workspace_id}/evaluations/runs/{run_id}` — per-question detail (question, retrieved chunks, generated answer, score, pass/fail).

## Metrics

- **Retrieval precision** — fraction of retrieved chunks that belong to
  an `expected_source` document (null when a row has no expected source).
- **Context relevance** — mean cosine similarity between the question
  embedding and each retrieved chunk's embedding.
- **Answer faithfulness** — LLM-as-judge score (0-1) for whether the
  generated answer's claims are grounded in the retrieved sources.
- **Answer relevancy** — cosine similarity between the question and the
  generated answer's embedding.
- **Hallucination rate** — share of items whose faithfulness score falls
  below `EVALUATION_HALLUCINATION_THRESHOLD` (default 0.5).
- **Latency** — retrieval / generation / total wall-clock time per item.
- **Token usage** — prompt/completion tokens from the LLM provider's
  usage metadata, or a `tiktoken` estimate when the provider doesn't
  report it.

An item's composite `score` is the mean of the metrics that apply to it
(retrieval precision is skipped when there's no expected source), and it
`passed` when that score clears `EVALUATION_PASS_THRESHOLD` (default 0.6)
and the answer wasn't flagged as hallucinated.
