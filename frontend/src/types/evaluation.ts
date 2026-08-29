export type RetrievalLevel = 1 | 2 | 3;

export interface EvaluationDatasetItem {
  question: string;
  expected_answer: string;
  expected_source: string[];
}

export interface EvaluationRunRequest {
  name?: string | null;
  items: EvaluationDatasetItem[];
  retrieval_level: RetrievalLevel;
  top_k?: number | null;
  pass_threshold?: number | null;
}

export interface RetrievedChunkResult {
  chunk_id: string;
  document_id: string;
  document_name: string | null;
  chunk_index: number;
  page_number: number | null;
  content_preview: string;
  score: number;
}

export interface TokenUsageResult {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated: boolean;
}

export interface LatencyResult {
  retrieval_ms: number;
  generation_ms: number;
  total_ms: number;
}

export interface EvaluationItemResult {
  id: string;
  question: string;
  expected_answer: string;
  expected_source: string[];
  generated_answer: string;
  retrieved_chunks: RetrievedChunkResult[];
  retrieval_precision: number | null;
  context_relevance: number;
  answer_faithfulness: number;
  answer_relevancy: number;
  hallucinated: boolean;
  judge_reasoning: string | null;
  latency: LatencyResult;
  token_usage: TokenUsageResult;
  score: number;
  passed: boolean;
  error: string | null;
}

export interface EvaluationRunSummary {
  id: string;
  workspace_id: string;
  name: string | null;
  item_count: number;
  passed_count: number;
  pass_rate: number;
  avg_retrieval_precision: number | null;
  avg_context_relevance: number;
  avg_answer_faithfulness: number;
  avg_answer_relevancy: number;
  hallucination_rate: number;
  avg_latency_ms: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  created_at: string;
}

export interface EvaluationRunResponse extends EvaluationRunSummary {
  items: EvaluationItemResult[];
}

export interface EvaluationRunListResponse {
  items: EvaluationRunSummary[];
  total: number;
}

export interface EvaluationDatasetParseResponse {
  items: EvaluationDatasetItem[];
}
