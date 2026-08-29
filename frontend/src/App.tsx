import { useState } from "react";

import { ChatPage } from "./pages/ChatPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { WorkspacePage } from "./pages/WorkspacePage";

type Tab = "documents" | "chat" | "evaluation";

export default function App() {
  const [workspaceId, setWorkspaceId] = useState(
    () => window.localStorage.getItem("workspaceId") ?? "",
  );

  const [activeTab, setActiveTab] = useState<Tab>("documents");

  const handleWorkspaceIdChange = (value: string) => {
    setWorkspaceId(value);
    window.localStorage.setItem("workspaceId", value);
  };

  return (
    <div className="app">
      <header className="app__header">
        <h1>AI Enterprise Knowledge Platform</h1>

        <label className="app__workspace-input">
          Workspace ID
          <input
            type="text"
            value={workspaceId}
            placeholder="Paste a workspace UUID"
            onChange={(event) =>
              handleWorkspaceIdChange(event.target.value)
            }
          />
        </label>

        {workspaceId && (
          <nav className="app__tabs">
            <button
              type="button"
              data-active={activeTab === "documents"}
              onClick={() => setActiveTab("documents")}
            >
              Documents
            </button>

            <button
              type="button"
              data-active={activeTab === "chat"}
              onClick={() => setActiveTab("chat")}
            >
              Chat
            </button>

            <button
              type="button"
              data-active={activeTab === "evaluation"}
              onClick={() => setActiveTab("evaluation")}
            >
              Evaluation
            </button>
          </nav>
        )}
      </header>

      {!workspaceId && (
        <p className="app__hint">
          Enter a workspace ID to upload documents and ask questions.
        </p>
      )}

      {workspaceId && activeTab === "documents" && (
        <WorkspacePage workspaceId={workspaceId} />
      )}

      {workspaceId && activeTab === "chat" && (
        <ChatPage workspaceId={workspaceId} />
      )}

      {workspaceId && activeTab === "evaluation" && (
        <EvaluationPage workspaceId={workspaceId} />
      )}
    </div>
  );
}