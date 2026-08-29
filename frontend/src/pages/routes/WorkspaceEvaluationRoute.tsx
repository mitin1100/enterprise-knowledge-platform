import { useParams } from "react-router-dom";

import { EvaluationPage } from "../EvaluationPage";

export function WorkspaceEvaluationRoute() {
  const { workspaceId } = useParams<{ workspaceId: string }>();

  if (!workspaceId) {
    return null;
  }

  return <EvaluationPage workspaceId={workspaceId} />;
}
