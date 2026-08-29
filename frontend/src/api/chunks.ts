import { apiClient } from "./client";
import type { ChunkContext } from "../types/chunk";

export async function getChunkContext(
  documentId: string,
  chunkIndex: number,
): Promise<ChunkContext> {
  const response = await apiClient.get<ChunkContext>(
    `/${documentId}/chunks/${chunkIndex}/context`,
  );

  return response.data;
}
