/**
 * API Types for FinVault AI Backend Integration
 */

export interface QueryRequest {
  query: string;
  mode: "quick" | "deep";
  tickers?: string[];
  retrieval_mode?: "numeric" | "narrative" | "hybrid";
}

export interface SourceReference {
  doc_type: string;
  ticker: string;
  year: number;
  section?: string;
  similarity_score?: number;
}

export interface QueryResponse {
  query: string;
  analysis: string;
  retrieval_mode: string;
  model_used: string;
  numeric_data_count: number;
  narrative_chunks_count: number;
  sources: SourceReference[];
  latency_ms: number;
  tokens_used?: number;
  contradictions_detected?: string;
}

export interface MemoryPreferences {
  risk_tolerance: "conservative" | "moderate" | "aggressive";
  focus_sectors: string[];
  key_metrics: string[];
  save_queries: boolean;
  max_history: number;
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  mode: "quick" | "deep";
  timestamp: Date;
  retrieval_mode: string;
  has_contradictions: boolean;
}
