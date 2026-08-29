import { apiClient } from "./client";
import type {
  EvaluationDatasetParseResponse,
  EvaluationRunListResponse,
  EvaluationRunRequest,
  EvaluationRunResponse,
} from "../types/evaluation";

export async function parseEvaluationDataset(
  workspaceId: string,
  file: File,
): Promise<EvaluationDatasetParseResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<EvaluationDatasetParseResponse>(
    `/workspaces/${workspaceId}/evaluations/datasets/parse`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data;
}

export async function createEvaluationRun(
  workspaceId: string,
  payload: EvaluationRunRequest,
): Promise<EvaluationRunResponse> {
  const response = await apiClient.post<EvaluationRunResponse>(
    `/workspaces/${workspaceId}/evaluations/runs`,
    payload,
  );

  return response.data;
}

export async function getEvaluationRuns(
  workspaceId: string,
): Promise<EvaluationRunListResponse> {
  const response = await apiClient.get<EvaluationRunListResponse>(
    `/workspaces/${workspaceId}/evaluations/runs`,
  );

  return response.data;
}

export async function getEvaluationRun(
  workspaceId: string,
  runId: string,
): Promise<EvaluationRunResponse> {
  const response = await apiClient.get<EvaluationRunResponse>(
    `/workspaces/${workspaceId}/evaluations/runs/${runId}`,
  );

  return response.data;
}
