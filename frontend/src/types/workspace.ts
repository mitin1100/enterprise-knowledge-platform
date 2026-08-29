export interface WorkspaceItem {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  created_at: string;
}

export interface WorkspaceCreateRequest {
  name: string;
  description?: string | null;
}
