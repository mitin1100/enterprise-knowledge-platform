import { useCallback, useEffect, useState } from "react";

import { createWorkspace, getWorkspaces } from "../api/workspaces";
import type { WorkspaceItem } from "../types/workspace";

export function useWorkspaces() {
  const [workspaces, setWorkspaces] = useState<WorkspaceItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const loadWorkspaces = useCallback(async () => {
    setIsLoading(true);

    try {
      const items = await getWorkspaces();
      setWorkspaces(items);
      setError(null);
    } catch {
      setError("Unable to load workspaces.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkspaces();
  }, [loadWorkspaces]);

  const addWorkspace = useCallback(
    async (name: string, description: string) => {
      setIsCreating(true);
      setError(null);

      try {
        const workspace = await createWorkspace({
          name,
          description: description || null,
        });

        setWorkspaces((current) => [workspace, ...current]);
        return workspace;
      } catch {
        setError("Unable to create workspace.");
        return null;
      } finally {
        setIsCreating(false);
      }
    },
    [],
  );

  return {
    workspaces,
    isLoading,
    isCreating,
    error,
    addWorkspace,
    refresh: loadWorkspaces,
  };
}
