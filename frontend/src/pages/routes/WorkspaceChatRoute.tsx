import { useParams } from "react-router-dom";

import { ChatPage } from "../ChatPage";

export function WorkspaceChatRoute() {
  const { workspaceId } = useParams<{ workspaceId: string }>();

  if (!workspaceId) {
    return null;
  }

  return <ChatPage workspaceId={workspaceId} />;
}
