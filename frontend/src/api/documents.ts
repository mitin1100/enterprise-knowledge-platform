import { apiClient } from "./client";
import type {
  DocumentItem,
  DocumentListResponse,
  DocumentUploadResponse,
} from "../types/document";

export async function uploadDocument(
  workspaceId: string,
  file: File,
  onProgress?: (percentage: number) => void,
): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<DocumentUploadResponse>(
    `/workspaces/${workspaceId}/documents`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (event) => {
        if (!event.total || !onProgress) {
          return;
        }

        const percentage = Math.round(
          (event.loaded * 100) / event.total,
        );

        onProgress(percentage);
      },
    },
  );

  return response.data.document;
}

export async function getDocuments(
  workspaceId: string,
): Promise<DocumentListResponse> {
  const response = await apiClient.get<DocumentListResponse>(
    `/workspaces/${workspaceId}/documents`,
  );

  return response.data;
}

export async function getDocument(
  workspaceId: string,
  documentId: string,
): Promise<DocumentItem> {
  const response = await apiClient.get<DocumentItem>(
    `/workspaces/${workspaceId}/documents/${documentId}`,
  );

  return response.data;
}
