/**
 * Query Panel Component
 * Handles user input, mode selection, and query submission
 */

"use client";

import React, { useState } from "react";
import { QueryRequest } from "@/types";
import { Search, Loader2 } from "lucide-react";

interface QueryPanelProps {
  onSubmit: (request: QueryRequest) => void;
  isLoading: boolean;
}

export const QueryPanel: React.FC<QueryPanelProps> = ({
  onSubmit,
  isLoading,
}) => {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"quick" | "deep">("quick");
  const [tickers, setTickers] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    onSubmit({
      query: query.trim(),
      mode,
      tickers: tickers
        .split(",")
        .map((t) => t.trim().toUpperCase())
        .filter((t) => t),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-gray-200 bg-white p-6">
      {/* Query Input */}
      <div>
        <label className="block text-sm font-medium text-gray-900 mb-2">
          Financial Query
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., What is Apple's revenue growth compared to Microsoft?"
          disabled={isLoading}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 resize-none"
          rows={4}
        />
      </div>

      {/* Mode and Ticker Selection */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Query Mode
          </label>
          <div className="flex gap-2">
            {(["quick", "deep"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                disabled={isLoading}
                className={`flex-1 py-2 px-3 rounded-md transition-colors ${
                  mode === m
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-900 hover:bg-gray-200"
                } disabled:opacity-50 disabled:cursor-not-allowed capitalize font-medium`}
              >
                {m}
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {mode === "quick"
              ? "Fast search - 3.5s typical latency"
              : "Deep analysis - 10-30s typical latency"}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Tickers (Optional)
          </label>
          <input
            type="text"
            value={tickers}
            onChange={(e) => setTickers(e.target.value)}
            placeholder="e.g., AAPL, MSFT"
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
          />
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Search
            </>
          )}
        </button>
      </div>
    </form>
  );
};
