import { useCallback, useEffect, useState } from "react";

import { getDocuments } from "../api/documents";
import type { DocumentItem } from "../types/document";

export function useDocuments(workspaceId: string) {
  const [documents, setDocuments] =
    useState<DocumentItem[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    try {
      const result = await getDocuments(workspaceId);
      setDocuments(result.items);
      setError(null);
    } catch {
      setError("Unable to load documents.");
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    const hasProcessingDocuments = documents.some(
      (document) =>
        document.status === "pending" ||
        document.status === "processing",
    );

    if (!hasProcessingDocuments) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadDocuments();
    }, 3000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [documents, loadDocuments]);

  function addDocument(document: DocumentItem) {
    setDocuments((current) => [
      document,
      ...current,
    ]);
  }

  return {
    documents,
    isLoading,
    error,
    addDocument,
    refresh: loadDocuments,
  };
}
