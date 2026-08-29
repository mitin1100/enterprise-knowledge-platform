import { useState, type FormEvent } from "react";

import { useChat } from "../../hooks/useChat";
import type { Citation } from "../../types/chat";
import { CitationViewer } from "./CitationViewer";
import { ConversationSidebar } from "./ConversationSidebar";
import { MessageBubble } from "./MessageBubble";

interface ChatBoxProps {
  workspaceId: string;
}

export function ChatBox({ workspaceId }: ChatBoxProps) {
  const {
    conversations,
    conversationId,
    messages,
    isLoading,
    isSending,
    error,
    ask,
    selectConversation,
    startConversation,
    renameActiveConversation,
    removeConversation,
  } = useChat(workspaceId);

  const [question, setQuestion] = useState("");
  const [activeCitation, setActiveCitation] = useState<Citation | null>(
    null,
  );

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const text = question.trim();

    if (!text || isSending) {
      return;
    }

    setQuestion("");
    await ask(text);
  };

  return (
    <div className="chat-box-layout">
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={conversationId}
        onSelect={selectConversation}
        onCreate={startConversation}
        onRename={renameActiveConversation}
        onDelete={removeConversation}
      />

      <div className="chat-box">
        <div className="chat-box__messages">
          {isLoading && <p>Loading conversation...</p>}

          {!isLoading && messages.length === 0 && (
            <p>Ask a question about your workspace documents.</p>
          )}

          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onSelectCitation={setActiveCitation}
            />
          ))}

          {isSending && <p className="chat-box__typing">Thinking...</p>}
        </div>

        {error && <p role="alert">{error}</p>}

        <form className="chat-box__form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={question}
            placeholder="Ask a question..."
            disabled={isLoading || isSending}
            onChange={(event) => setQuestion(event.target.value)}
          />

          <button
            type="submit"
            disabled={isLoading || isSending || !question.trim()}
          >
            Send
          </button>
        </form>

        {activeCitation && (
          <CitationViewer
            citation={activeCitation}
            onClose={() => setActiveCitation(null)}
          />
        )}
      </div>
    </div>
  );
}
