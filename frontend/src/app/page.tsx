"use client";

import React, { useState, useEffect } from "react";
import LoginPage from "@/components/LoginPage";
import { useAuth } from "@/lib/AuthContext";
import {
  QueryPanel,
  ResultsView,
  MemoryPreferencesSidebar,
  SourcesView,
  QueryHistory,
  MetricsFooter,
} from "@/components";
import { useQueryFinancialData, useBackendQueryHistory } from "@/hooks/index";
import { QueryRequest, QueryResponse, QueryHistoryItem } from "@/types";
import { saveQueryToHistory } from "@/lib/api";
import { Zap, LogOut, Plus } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

export default function Home() {
  // ALL HOOKS MUST BE CALLED FIRST - before any conditional logic
  const { token, username, logout, isAuthenticated } = useAuth();
  const { history, isLoading: historyLoading, clearHistory } = useBackendQueryHistory(token);
  const queryClient = useQueryClient();
  const [isMounted, setIsMounted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedHistoryQuery, setSelectedHistoryQuery] = useState<string | undefined>(undefined);
  const [currentQueryId, setCurrentQueryId] = useState<number | string | undefined>(undefined);
  const { mutate: queryData, isPending } = useQueryFinancialData();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Mark component as mounted after hydration
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleSubmit = (request: QueryRequest) => {
    setError(null);
    setResponse(null);

    queryData(request, {
      onSuccess: (data) => {
        setResponse(data);
        
        // Save to backend if authenticated
        if (token) {
          saveQueryToHistory(
            request.query,
            token,
            request.mode || "quick",
            request.retrieval_mode || "hybrid",
            data.analysis,
            data.model_used,
            data.latency_ms
          ).then(() => {
            // Refetch query history after save
            queryClient.invalidateQueries({ queryKey: ["queryHistory", token] });
          }).catch((err) => {
            console.warn("Failed to save to backend history:", err);
          });
        }
      },
      onError: (err: any) => {
        setError(
          err.message || "Failed to query financial data. Please try again."
        );
      },
    });
  };

  const handleSelectFromHistory = (item: QueryHistoryItem) => {
    setError(null);
    // Populate the query panel with the selected query
    setSelectedHistoryQuery(item.query);
    setCurrentQueryId(item.id);
    
    // Reconstruct and display the response from history
    const reconstructedResponse: QueryResponse = {
      query: item.query,
      analysis: item.analysis || "No analysis available",
      retrieval_mode: item.retrieval_mode || "hybrid",
      model_used: item.model_used || "unknown",
      numeric_data_count: 0,
      narrative_chunks_count: 0,
      sources: [],
      latency_ms: item.latency_ms || 0,
    };
    setResponse(reconstructedResponse);
  };

  const handleNewChat = () => {
    // Clear all current state to start fresh
    setResponse(null);
    setError(null);
    setSelectedHistoryQuery(undefined);
    setCurrentQueryId(undefined);
  };

  // NOW check authentication and return early if needed
  // Wait for hydration to complete before showing authenticated content
  if (!isMounted || !isAuthenticated) {
    return (
      <LoginPage
        apiUrl={apiUrl}
      />
    );
  }

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
              <div>
                <h1 className="text-2xl font-bold text-gray-900">FinVault AI</h1>
                <p className="text-sm text-gray-600">Logged in as {username}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="px-4 py-2 bg-gray-100 text-gray-900 rounded-md hover:bg-gray-200 font-medium transition-colors"
              >
                Memory
              </button>
              {currentQueryId && (
                <button
                  onClick={handleNewChat}
                  title="Start a new chat"
                  className="px-4 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 font-medium transition-colors flex items-center gap-2"
                >
                  <Plus size={18} />
                  New Chat
                </button>
              )}
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 font-medium transition-colors flex items-center gap-2"
              >
                <LogOut size={18} />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Query Panel */}
            <QueryPanel 
              onSubmit={handleSubmit} 
              isLoading={isPending}
              initialQuery={selectedHistoryQuery}
            />

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
              items={history}
              isLoading={historyLoading}
              currentQueryId={currentQueryId}
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
