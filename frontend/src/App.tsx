import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { WorkspaceLayout } from "./components/layout/WorkspaceLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { WorkspaceChatRoute } from "./pages/routes/WorkspaceChatRoute";
import { WorkspaceDocumentsRoute } from "./pages/routes/WorkspaceDocumentsRoute";
import { WorkspaceEvaluationRoute } from "./pages/routes/WorkspaceEvaluationRoute";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />

        <Route path="/workspaces/:workspaceId" element={<WorkspaceLayout />}>
          <Route index element={<Navigate to="documents" replace />} />
          <Route path="documents" element={<WorkspaceDocumentsRoute />} />
          <Route path="chat" element={<WorkspaceChatRoute />} />
          <Route path="evaluation" element={<WorkspaceEvaluationRoute />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
