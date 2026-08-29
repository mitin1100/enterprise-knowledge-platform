import { useCallback, useEffect, useRef, useState } from "react";

import {
  createConversation,
  deleteConversation,
  getConversations,
  getMessages,
  renameConversation,
  sendMessage,
} from "../api/chat";
import type { ConversationItem, MessageItem } from "../types/chat";

export function useChat(workspaceId: string) {
  const [conversations, setConversations] = useState<ConversationItem[]>(
    [],
  );
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initializedFor = useRef<string | null>(null);

  const loadMessages = useCallback(
    async (id: string) => {
      const { items } = await getMessages(workspaceId, id);
      setMessages(items);
    },
    [workspaceId],
  );

  useEffect(() => {
    if (initializedFor.current === workspaceId) {
      return;
    }

    initializedFor.current = workspaceId;

    const initialize = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const { items } = await getConversations(workspaceId);

        const activeItems =
          items.length > 0 ? items : [await createConversation(workspaceId)];

        setConversations(activeItems);
        setConversationId(activeItems[0].id);

        await loadMessages(activeItems[0].id);
      } catch {
        setError("Unable to start the conversation.");
      } finally {
        setIsLoading(false);
      }
    };

    void initialize();
  }, [workspaceId, loadMessages]);

  const selectConversation = useCallback(
    async (id: string) => {
      if (id === conversationId) {
        return;
      }

      setConversationId(id);
      setIsLoading(true);
      setError(null);

      try {
        await loadMessages(id);
      } catch {
        setError("Unable to load this conversation.");
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, loadMessages],
  );

  const startConversation = useCallback(async () => {
    setError(null);

    try {
      const conversation = await createConversation(workspaceId);

      setConversations((current) => [conversation, ...current]);
      setConversationId(conversation.id);
      setMessages([]);
    } catch {
      setError("Unable to start a new conversation.");
    }
  }, [workspaceId]);

  const renameActiveConversation = useCallback(
    async (id: string, title: string) => {
      const trimmed = title.trim();

      if (!trimmed) {
        return;
      }

      setError(null);

      try {
        const updated = await renameConversation(workspaceId, id, trimmed);

        setConversations((current) =>
          current.map((conversation) =>
            conversation.id === id ? updated : conversation,
          ),
        );
      } catch {
        setError("Unable to rename the conversation.");
      }
    },
    [workspaceId],
  );

  const removeConversation = useCallback(
    async (id: string) => {
      setError(null);

      try {
        await deleteConversation(workspaceId, id);

        const remaining = conversations.filter(
          (conversation) => conversation.id !== id,
        );

        setConversations(remaining);

        if (id !== conversationId) {
          return;
        }

        if (remaining.length > 0) {
          setConversationId(remaining[0].id);
          await loadMessages(remaining[0].id);
          return;
        }

        const conversation = await createConversation(workspaceId);

        setConversations([conversation]);
        setConversationId(conversation.id);
        setMessages([]);
      } catch {
        setError("Unable to delete the conversation.");
      }
    },
    [workspaceId, conversations, conversationId, loadMessages],
  );

  const ask = useCallback(
    async (question: string) => {
      if (!conversationId || !question.trim()) {
        return;
      }

      setIsSending(true);
      setError(null);

      try {
        const response = await sendMessage(
          workspaceId,
          conversationId,
          question,
        );

        setMessages((current) => [
          ...current,
          response.user_message,
          response.assistant_message,
        ]);
      } catch {
        setError("Unable to get an answer. Please try again.");
      } finally {
        setIsSending(false);
      }
    },
    [workspaceId, conversationId],
  );

  return {
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
  };
}
