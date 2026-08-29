import { useCallback, useEffect, useState } from "react";

import {
  createEvaluationRun,
  getEvaluationRun,
  getEvaluationRuns,
  parseEvaluationDataset,
} from "../api/evaluation";
import type {
  EvaluationDatasetItem,
  EvaluationRunResponse,
  EvaluationRunSummary,
  RetrievalLevel,
} from "../types/evaluation";

export function useEvaluation(workspaceId: string) {
  const [runs, setRuns] = useState<EvaluationRunSummary[]>([]);
  const [selectedRun, setSelectedRun] =
    useState<EvaluationRunResponse | null>(null);

  const [datasetItems, setDatasetItems] =
    useState<EvaluationDatasetItem[]>([]);

  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [isParsingDataset, setIsParsingDataset] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRuns = useCallback(async () => {
    try {
      const result = await getEvaluationRuns(workspaceId);
      setRuns(result.items);
    } catch {
      setError("Unable to load evaluation runs.");
    } finally {
      setIsLoadingRuns(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  async function uploadDatasetFile(file: File) {
    try {
      setIsParsingDataset(true);
      setError(null);

      const result = await parseEvaluationDataset(workspaceId, file);
      setDatasetItems(result.items);
    } catch {
      setError("Unable to parse the dataset file.");
    } finally {
      setIsParsingDataset(false);
    }
  }

  async function runEvaluation(
    retrievalLevel: RetrievalLevel,
    name?: string,
  ) {
    if (datasetItems.length === 0) {
      setError("Load a dataset before running an evaluation.");
      return;
    }

    try {
      setIsRunning(true);
      setError(null);

      const run = await createEvaluationRun(workspaceId, {
        name: name || null,
        items: datasetItems,
        retrieval_level: retrievalLevel,
      });

      setSelectedRun(run);
      setRuns((current) => [run, ...current]);
    } catch {
      setError("Evaluation run failed.");
    } finally {
      setIsRunning(false);
    }
  }

  async function viewRun(runId: string) {
    try {
      setError(null);
      const run = await getEvaluationRun(workspaceId, runId);
      setSelectedRun(run);
    } catch {
      setError("Unable to load that evaluation run.");
    }
  }

  return {
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
    clearDataset: () => setDatasetItems([]),
  };
}
