export type MessageRole = "USER" | "ASSISTANT" | "SYSTEM";

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_name: string | null;
  chunk_index: number;
  page_number: number | null;
  chunk_preview: string;
  score: number;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ConversationItem {
  id: string;
  workspace_id: string;
  user_id: string;
  title: string | null;
  created_at: string;
}

export interface ConversationListResponse {
  items: ConversationItem[];
  total: number;
}

export interface MessageListResponse {
  items: MessageItem[];
  total: number;
}

export interface ChatResponse {
  conversation_id: string;
  user_message: MessageItem;
  assistant_message: MessageItem;
}
