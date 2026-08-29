import { ChatBox } from "../components/chat/ChatBox";

interface ChatPageProps {
  workspaceId: string;
}

export function ChatPage({ workspaceId }: ChatPageProps) {
  return (
    <main>
      <header>
        <h1>Ask your documents</h1>
        <p>
          Answers are grounded in your workspace documents. Click a source
          to see the exact passage it came from.
        </p>
      </header>

      <ChatBox workspaceId={workspaceId} />
    </main>
  );
}
