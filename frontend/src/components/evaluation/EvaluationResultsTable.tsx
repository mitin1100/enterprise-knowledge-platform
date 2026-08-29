import { Fragment, useState } from "react";

import type { EvaluationItemResult } from "../../types/evaluation";

interface EvaluationResultsTableProps {
  items: EvaluationItemResult[];
}

function formatScore(value: number | null): string {
  return value === null ? "n/a" : value.toFixed(2);
}

export function EvaluationResultsTable({
  items,
}: EvaluationResultsTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (items.length === 0) {
    return <p>This run has no results.</p>;
  }

  return (
    <table className="evaluation-results-table">
      <thead>
        <tr>
          <th>Question</th>
          <th>Retrieved chunks</th>
          <th>Generated answer</th>
          <th>Score</th>
          <th>Pass/Fail</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => {
          const isExpanded = expandedId === item.id;

          return (
            <Fragment key={item.id}>
              <tr
                className="evaluation-results-table__row"
                onClick={() =>
                  setExpandedId(isExpanded ? null : item.id)
                }
              >
                <td>{item.question}</td>
                <td>{item.retrieved_chunks.length}</td>
                <td className="evaluation-results-table__answer">
                  {item.error ? (
                    <span className="evaluation-results-table__error">
                      {item.error}
                    </span>
                  ) : (
                    item.generated_answer
                  )}
                </td>
                <td>{formatScore(item.score)}</td>
                <td>
                  <span
                    className="evaluation-results-table__badge"
                    data-passed={item.passed}
                  >
                    {item.passed ? "Pass" : "Fail"}
                  </span>
                  {item.hallucinated && (
                    <span className="evaluation-results-table__hallucination">
                      hallucinated
                    </span>
                  )}
                </td>
              </tr>

              {isExpanded && (
                <tr className="evaluation-results-table__detail-row">
                  <td colSpan={5}>
                    <div className="evaluation-results-table__detail">
                      <div>
                        <h4>Metrics</h4>
                        <ul>
                          <li>
                            Retrieval precision:{" "}
                            {formatScore(item.retrieval_precision)}
                          </li>
                          <li>
                            Context relevance:{" "}
                            {formatScore(item.context_relevance)}
                          </li>
                          <li>
                            Answer faithfulness:{" "}
                            {formatScore(item.answer_faithfulness)}
                          </li>
                          <li>
                            Answer relevancy:{" "}
                            {formatScore(item.answer_relevancy)}
                          </li>
                          <li>
                            Latency: {Math.round(item.latency.total_ms)} ms
                            (retrieval {Math.round(item.latency.retrieval_ms)}
                            ms, generation{" "}
                            {Math.round(item.latency.generation_ms)}ms)
                          </li>
                          <li>
                            Tokens: {item.token_usage.total_tokens}
                            {item.token_usage.estimated
                              ? " (estimated)"
                              : ""}
                          </li>
                        </ul>

                        {item.judge_reasoning && (
                          <p className="evaluation-results-table__reasoning">
                            Judge: {item.judge_reasoning}
                          </p>
                        )}
                      </div>

                      <div>
                        <h4>Retrieved chunks</h4>
                        <ol>
                          {item.retrieved_chunks.map((chunk) => (
                            <li key={chunk.chunk_id}>
                              <strong>
                                {chunk.document_name || chunk.document_id}
                              </strong>{" "}
                              (score {chunk.score.toFixed(2)})
                              <p>{chunk.content_preview}</p>
                            </li>
                          ))}
                        </ol>
                      </div>

                      {item.expected_answer && (
                        <div>
                          <h4>Expected answer</h4>
                          <p>{item.expected_answer}</p>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
