export interface ChunkItem {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  page_number: number | null;
  token_count: number;
  embedding_id: string | null;
  chunk_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ChunkContext {
  document_id: string;
  document_name: string;
  chunk: ChunkItem;
  previous: ChunkItem | null;
  next: ChunkItem | null;
}
