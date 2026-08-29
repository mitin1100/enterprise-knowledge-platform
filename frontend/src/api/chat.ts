import { apiClient } from "./client";
import type {
  ChatResponse,
  ConversationItem,
  ConversationListResponse,
  MessageListResponse,
} from "../types/chat";

export async function createConversation(
  workspaceId: string,
  title?: string,
): Promise<ConversationItem> {
  const response = await apiClient.post<ConversationItem>(
    `/workspaces/${workspaceId}/conversations`,
    { title: title ?? null },
  );

  return response.data;
}

export async function getConversations(
  workspaceId: string,
): Promise<ConversationListResponse> {
  const response = await apiClient.get<ConversationListResponse>(
    `/workspaces/${workspaceId}/conversations`,
  );

  return response.data;
}

export async function getMessages(
  workspaceId: string,
  conversationId: string,
): Promise<MessageListResponse> {
  const response = await apiClient.get<MessageListResponse>(
    `/workspaces/${workspaceId}/conversations/${conversationId}/messages`,
  );

  return response.data;
}

export async function sendMessage(
  workspaceId: string,
  conversationId: string,
  message: string,
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>(
    `/workspaces/${workspaceId}/conversations/${conversationId}/messages`,
    { message },
  );

  return response.data;
}
