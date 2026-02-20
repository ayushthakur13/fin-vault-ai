"use client";

import React, { useState, useEffect } from "react";
import {
  QueryPanel,
  ResultsView,
  MemoryPreferencesSidebar,
  SourcesView,
  QueryHistory,
  MetricsFooter,
} from "@/components";
import { useQueryFinancialData, useQueryHistory } from "@/hooks/index";
import { QueryRequest, QueryResponse, QueryHistoryItem } from "@/types";
import { Zap } from "lucide-react";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { mutate: queryData, isPending } = useQueryFinancialData();
  const { history, addToHistory, clearHistory } = useQueryHistory();
  const [historyItems, setHistoryItems] = useState<QueryHistoryItem[]>([]);

  useEffect(() => {
    // Convert history to QueryHistoryItem format
    setHistoryItems(
      history.map((item: any) => ({
        id: item.id,
        query: item.query,
        mode: "quick" as const,
        timestamp: new Date(item.timestamp),
        retrieval_mode: "hybrid",
        has_contradictions: false,
      }))
    );
  }, [history]);

  const handleSubmit = (request: QueryRequest) => {
    setError(null);
    setResponse(null);

    queryData(request, {
      onSuccess: (data) => {
        setResponse(data);
        addToHistory(request.query);
      },
      onError: (err: any) => {
        setError(
          err.message || "Failed to query financial data. Please try again."
        );
      },
    });
  };

  const handleSelectFromHistory = (query: string) => {
    setResponse(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900">FinVault AI</h1>
            </div>
            <button
              onClick={() => setSidebarOpen(true)}
              className="px-4 py-2 bg-gray-100 text-gray-900 rounded-md hover:bg-gray-200 font-medium transition-colors"
            >
              Memory
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Query Panel */}
            <QueryPanel onSubmit={handleSubmit} isLoading={isPending} />

            {/* Error Message */}
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Results */}
            {response && !error && (
              <>
                <ResultsView response={response} />
                <SourcesView sources={response.sources || []} />
              </>
            )}

            {/* Empty State */}
            {!response && !error && !isPending && (
              <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Start Your Financial Analysis
                </h3>
                <p className="text-gray-600">
                  Ask questions about companies, financial metrics, and
                  investment insights. Our hybrid retrieval system combines
                  structured data with narrative analysis.
                </p>
              </div>
            )}
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-6">
            <QueryHistory
              items={historyItems}
              onSelect={handleSelectFromHistory}
              onClear={clearHistory}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      {response && (
        <MetricsFooter
          latencyMs={response.latency_ms}
          tokensUsed={response.tokens_used}
          modelUsed={response.model_used}
          retrievalMode={response.retrieval_mode}
        />
      )}

      {/* Memory Preferences Sidebar */}
      <MemoryPreferencesSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
    </div>
  );
}
