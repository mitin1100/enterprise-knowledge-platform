export type DocumentStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export type StorageProvider = "local" | "minio";

export interface DocumentItem {
  id: string;
  workspace_id: string;
  original_filename: string;
  mime_type: string;
  file_extension: string;
  file_size: number;
  checksum: string;
  status: DocumentStatus;
  storage_provider: StorageProvider;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  document: DocumentItem;
  message: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}
