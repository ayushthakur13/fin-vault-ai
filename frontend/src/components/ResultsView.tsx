/**
 * Results View Component
 * Displays structured query results with multiple panels
 */

"use client";

import React from "react";
import { QueryResponse } from "@/types";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface ResultsViewProps {
  response: QueryResponse;
}

export const ResultsView: React.FC<ResultsViewProps> = ({ response }) => {
  return (
    <div className="space-y-4">
      {/* Summary Panel */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Analysis Summary</h2>
        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
          {response.analysis}
        </p>
        {response.contradictions_detected && (
          <div className="mt-4 flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-md">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-900">Contradictions Detected</h3>
              <p className="text-sm text-amber-800 mt-1">{response.contradictions_detected}</p>
            </div>
          </div>
        )}
      </div>

      {/* Metrics Panel (if numeric data exists) */}
      {response.numeric_data_count > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h2>
          <p className="text-sm text-gray-600 mb-4">
            {response.numeric_data_count} data points from structured sources
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: "Revenue", value: "See sources" },
              { label: "Growth Rate", value: "See sources" },
              { label: "Net Margin", value: "See sources" },
              { label: "ROE", value: "See sources" },
              { label: "P/E Ratio", value: "See sources" },
              { label: "Debt/Equity", value: "See sources" },
            ].map((metric) => (
              <div
                key={metric.label}
                className="p-3 rounded-md bg-gray-50 border border-gray-200"
              >
                <p className="text-xs font-medium text-gray-600">{metric.label}</p>
                <p className="text-sm font-semibold text-gray-900 mt-1">
                  {metric.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Panel (if narratives exist) */}
      {response.narrative_chunks_count > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Evidence</h2>
          <p className="text-sm text-gray-600 mb-4">
            {response.narrative_chunks_count} supporting narrative chunks
          </p>
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="p-3 rounded-md bg-blue-50 border border-blue-200"
              >
                <p className="text-sm text-blue-900">
                  Supporting evidence from earnings transcript...
                </p>
                <p className="text-xs text-blue-700 mt-2">
                  Q4 2025 Earnings Call • Similarity: 0.92
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confidence Panel */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Confidence & Metadata</h2>
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-600">Retrieval Mode</label>
            <p className="text-gray-900 font-semibold capitalize mt-1">
              {response.retrieval_mode}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-600">Model Used</label>
            <p className="text-gray-900 font-semibold mt-1">{response.model_used}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-600">Query Processed</label>
            <p className="text-gray-900 mt-1 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              Successfully
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
