import type { EvaluationRunSummary } from "../../types/evaluation";

interface EvaluationSummaryProps {
  run: EvaluationRunSummary;
}

function formatPercent(value: number | null): string {
  return value === null ? "n/a" : `${Math.round(value * 100)}%`;
}

export function EvaluationSummary({ run }: EvaluationSummaryProps) {
  const metrics = [
    { label: "Pass rate", value: formatPercent(run.pass_rate) },
    {
      label: "Retrieval precision",
      value: formatPercent(run.avg_retrieval_precision),
    },
    {
      label: "Context relevance",
      value: formatPercent(run.avg_context_relevance),
    },
    {
      label: "Answer faithfulness",
      value: formatPercent(run.avg_answer_faithfulness),
    },
    {
      label: "Answer relevancy",
      value: formatPercent(run.avg_answer_relevancy),
    },
    {
      label: "Hallucination rate",
      value: formatPercent(run.hallucination_rate),
    },
    {
      label: "Avg latency",
      value: `${Math.round(run.avg_latency_ms)} ms`,
    },
    {
      label: "Total tokens",
      value: run.total_tokens.toLocaleString(),
    },
  ];

  return (
    <div className="evaluation-summary">
      {metrics.map((metric) => (
        <div className="evaluation-summary__card" key={metric.label}>
          <span className="evaluation-summary__label">{metric.label}</span>
          <span className="evaluation-summary__value">{metric.value}</span>
        </div>
      ))}
    </div>
  );
}
