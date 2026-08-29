import { apiClient } from "./client";
import type {
  WorkspaceCreateRequest,
  WorkspaceItem,
} from "../types/workspace";

export async function getWorkspaces(): Promise<WorkspaceItem[]> {
  const response = await apiClient.get<WorkspaceItem[]>("/workspaces");

  return response.data;
}

export async function getWorkspace(
  workspaceId: string,
): Promise<WorkspaceItem> {
  const response = await apiClient.get<WorkspaceItem>(
    `/workspaces/${workspaceId}`,
  );

  return response.data;
}

export async function createWorkspace(
  payload: WorkspaceCreateRequest,
): Promise<WorkspaceItem> {
  const response = await apiClient.post<WorkspaceItem>(
    "/workspaces",
    payload,
  );

  return response.data;
}

export async function deleteWorkspace(
  workspaceId: string,
): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}`);
}
