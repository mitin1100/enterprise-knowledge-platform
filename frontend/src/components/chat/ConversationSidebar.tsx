import { useState, type KeyboardEvent } from "react";

import type { ConversationItem } from "../../types/chat";

interface ConversationSidebarProps {
  conversations: ConversationItem[];
  activeConversationId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}: ConversationSidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");

  const startRename = (conversation: ConversationItem) => {
    setEditingId(conversation.id);
    setDraftTitle(conversation.title ?? "");
  };

  const commitRename = (id: string) => {
    onRename(id, draftTitle);
    setEditingId(null);
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLInputElement>,
    id: string,
  ) => {
    if (event.key === "Enter") {
      commitRename(id);
    } else if (event.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <aside className="conversation-sidebar">
      <button
        type="button"
        className="conversation-sidebar__new"
        onClick={onCreate}
      >
        New conversation
      </button>

      <ul className="conversation-sidebar__list">
        {conversations.map((conversation) => (
          <li
            key={conversation.id}
            className="conversation-sidebar__item"
            data-active={conversation.id === activeConversationId}
          >
            {editingId === conversation.id ? (
              <input
                autoFocus
                type="text"
                value={draftTitle}
                onChange={(event) => setDraftTitle(event.target.value)}
                onBlur={() => commitRename(conversation.id)}
                onKeyDown={(event) => handleKeyDown(event, conversation.id)}
              />
            ) : (
              <button
                type="button"
                className="conversation-sidebar__title"
                onClick={() => onSelect(conversation.id)}
                onDoubleClick={() => startRename(conversation)}
              >
                {conversation.title ?? "Untitled conversation"}
              </button>
            )}

            <div className="conversation-sidebar__actions">
              <button
                type="button"
                title="Rename"
                onClick={() => startRename(conversation)}
              >
                Rename
              </button>

              <button
                type="button"
                title="Delete"
                onClick={() => onDelete(conversation.id)}
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
