import { useEvaluation } from "../../hooks/useEvaluation";
import { DatasetUploader } from "./DatasetUploader";
import { EvaluationResultsTable } from "./EvaluationResultsTable";
import { EvaluationRunList } from "./EvaluationRunList";
import { EvaluationSummary } from "./EvaluationSummary";

interface EvaluationPanelProps {
  workspaceId: string;
}

export function EvaluationPanel({ workspaceId }: EvaluationPanelProps) {
  const {
    runs,
    selectedRun,
    datasetItems,
    isLoadingRuns,
    isParsingDataset,
    isRunning,
    error,
    uploadDatasetFile,
    runEvaluation,
    viewRun,
  } = useEvaluation(workspaceId);

  return (
    <main className="evaluation-panel">
      <header>
        <h1>Evaluation</h1>
        <p>
          Upload a dataset of questions, run it through the RAG
          pipeline, and review retrieval/answer quality metrics.
        </p>
      </header>

      {error && <p role="alert">{error}</p>}

      <section>
        <h2>Run a new evaluation</h2>
        <DatasetUploader
          datasetItems={datasetItems}
          isParsingDataset={isParsingDataset}
          isRunning={isRunning}
          onFileSelected={uploadDatasetFile}
          onRun={runEvaluation}
        />
      </section>

      <div className="evaluation-panel__layout">
        <section>
          <h2>Run history</h2>
          {isLoadingRuns ? (
            <p>Loading runs...</p>
          ) : (
            <EvaluationRunList
              runs={runs}
              selectedRunId={selectedRun?.id ?? null}
              onSelect={viewRun}
            />
          )}
        </section>

        <section className="evaluation-panel__dashboard">
          {selectedRun ? (
            <>
              <h2>{selectedRun.name || "Untitled run"}</h2>
              <EvaluationSummary run={selectedRun} />
              <EvaluationResultsTable items={selectedRun.items} />
            </>
          ) : (
            <p>Select a run to see its dashboard.</p>
          )}
        </section>
      </div>
    </main>
  );
}
