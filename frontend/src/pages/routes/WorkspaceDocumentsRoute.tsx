import { useParams } from "react-router-dom";

import { WorkspacePage } from "../WorkspacePage";

export function WorkspaceDocumentsRoute() {
  const { workspaceId } = useParams<{ workspaceId: string }>();

  if (!workspaceId) {
    return null;
  }

  return <WorkspacePage workspaceId={workspaceId} />;
}
