import type { EvaluationRunSummary } from "../../types/evaluation";

interface EvaluationRunListProps {
  runs: EvaluationRunSummary[];
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function EvaluationRunList({
  runs,
  selectedRunId,
  onSelect,
}: EvaluationRunListProps) {
  if (runs.length === 0) {
    return <p>No evaluation runs yet.</p>;
  }

  return (
    <ul className="evaluation-run-list">
      {runs.map((run) => (
        <li key={run.id}>
          <button
            type="button"
            className="evaluation-run-list__item"
            data-active={run.id === selectedRunId}
            onClick={() => onSelect(run.id)}
          >
            <span className="evaluation-run-list__name">
              {run.name || "Untitled run"}
            </span>
            <span className="evaluation-run-list__meta">
              {new Date(run.created_at).toLocaleString()} ·{" "}
              {run.item_count} question
              {run.item_count === 1 ? "" : "s"}
            </span>
            <span
              className="evaluation-run-list__pass-rate"
              data-passing={run.pass_rate >= 0.6}
            >
              {formatPercent(run.pass_rate)} passed · hallucination{" "}
              {formatPercent(run.hallucination_rate)}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
