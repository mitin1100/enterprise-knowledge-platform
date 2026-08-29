import { useEffect, useState } from "react";
import {
  NavLink,
  Outlet,
  useNavigate,
  useParams,
} from "react-router-dom";

import { getWorkspace } from "../../api/workspaces";
import { useAuth } from "../../context/AuthContext";
import type { WorkspaceItem } from "../../types/workspace";

export function WorkspaceLayout() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [workspace, setWorkspace] = useState<WorkspaceItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceId) {
      return;
    }

    getWorkspace(workspaceId)
      .then(setWorkspace)
      .catch(() => setError("Workspace not found."));
  }, [workspaceId]);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  if (!workspaceId) {
    return null;
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__header-title">
          <button
            type="button"
            className="workspace-layout__back"
            onClick={() => navigate("/dashboard")}
          >
            &larr; Dashboard
          </button>

          <h1>{workspace?.name ?? "Workspace"}</h1>
        </div>

        <nav className="app__tabs">
          <NavLink
            to={`/workspaces/${workspaceId}/documents`}
            className={({ isActive }) => (isActive ? "app__tab--active" : undefined)}
          >
            Documents
          </NavLink>

          <NavLink
            to={`/workspaces/${workspaceId}/chat`}
            className={({ isActive }) => (isActive ? "app__tab--active" : undefined)}
          >
            Chat
          </NavLink>

          <NavLink
            to={`/workspaces/${workspaceId}/evaluation`}
            className={({ isActive }) => (isActive ? "app__tab--active" : undefined)}
          >
            Evaluation
          </NavLink>
        </nav>

        <div className="app__header-actions">
          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      {error && <p role="alert">{error}</p>}

      <Outlet />
    </div>
  );
}
