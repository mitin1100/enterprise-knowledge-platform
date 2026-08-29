import { useNavigate } from "react-router-dom";

import type { WorkspaceItem } from "../../types/workspace";

interface WorkspaceListProps {
  workspaces: WorkspaceItem[];
}

export function WorkspaceList({ workspaces }: WorkspaceListProps) {
  const navigate = useNavigate();

  if (workspaces.length === 0) {
    return <p>No workspaces yet. Create one to get started.</p>;
  }

  return (
    <ul className="workspace-list">
      {workspaces.map((workspace) => (
        <li key={workspace.id}>
          <button
            type="button"
            className="workspace-list__card"
            onClick={() =>
              navigate(`/workspaces/${workspace.id}/documents`)
            }
          >
            <span className="workspace-list__name">{workspace.name}</span>

            {workspace.description && (
              <span className="workspace-list__description">
                {workspace.description}
              </span>
            )}

            <span className="workspace-list__meta">
              Created {new Date(workspace.created_at).toLocaleDateString()}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
