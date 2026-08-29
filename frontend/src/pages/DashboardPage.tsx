import { useNavigate } from "react-router-dom";

import { CreateWorkspaceForm } from "../components/workspace/CreateWorkspaceForm";
import { WorkspaceList } from "../components/workspace/WorkspaceList";
import { useAuth } from "../context/AuthContext";
import { useWorkspaces } from "../hooks/useWorkspaces";

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { workspaces, isLoading, isCreating, error, addWorkspace } =
    useWorkspaces();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <main className="app">
      <header className="app__header">
        <div className="app__header-title">
          <span className="eyebrow">Dashboard</span>
          <h1>Your workspaces</h1>
        </div>

        <div className="app__header-actions">
          {user && <span>{user.email}</span>}
          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      <section>
        <h2>Create workspace</h2>
        <CreateWorkspaceForm isCreating={isCreating} onCreate={addWorkspace} />
      </section>

      <section>
        <h2>Workspaces</h2>

        {isLoading && <p>Loading workspaces...</p>}
        {error && <p role="alert">{error}</p>}

        {!isLoading && <WorkspaceList workspaces={workspaces} />}
      </section>
    </main>
  );
}
