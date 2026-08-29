import { useCallback, useEffect, useRef, useState } from "react";

import {
  createConversation,
  getConversations,
  getMessages,
  sendMessage,
} from "../api/chat";
import type { MessageItem } from "../types/chat";

export function useChat(workspaceId: string) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initializedFor = useRef<string | null>(null);

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

        const conversation =
          items[0] ?? (await createConversation(workspaceId));

        setConversationId(conversation.id);

        const { items: history } = await getMessages(
          workspaceId,
          conversation.id,
        );

        setMessages(history);
      } catch {
        setError("Unable to start the conversation.");
      } finally {
        setIsLoading(false);
      }
    };

    void initialize();
  }, [workspaceId]);

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
    conversationId,
    messages,
    isLoading,
    isSending,
    error,
    ask,
  };
}
