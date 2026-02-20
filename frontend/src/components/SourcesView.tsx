/**
 * Sources and Traceability View
 * Shows query sources with expandable details
 */

"use client";

import React, { useState } from "react";
import { SourceReference } from "@/types";
import { ChevronDown, FileText, Database } from "lucide-react";

interface SourcesViewProps {
  sources: SourceReference[];
}

export const SourcesView: React.FC<SourcesViewProps> = ({ sources }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const groupedByType = sources.reduce(
    (acc, source) => {
      const key = source.doc_type;
      if (!acc[key]) acc[key] = [];
      acc[key].push(source);
      return acc;
    },
    {} as Record<string, SourceReference[]>
  );

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Sources & Traceability</h2>

      <div className="space-y-3">
        {Object.entries(groupedByType).map(([docType, items]) => (
          <div key={docType} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* Source Type Header */}
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {docType === "structured_metric" ? (
                    <Database className="w-5 h-5 text-blue-600" />
                  ) : (
                    <FileText className="w-5 h-5 text-green-600" />
                  )}
                  <span className="font-medium text-gray-900 capitalize">
                    {docType === "structured_metric"
                      ? "Structured Metrics"
                      : docType === "earnings_call"
                        ? "Earnings Calls"
                        : "Narratives"}
                  </span>
                  <span className="text-sm text-gray-600">({items.length})</span>
                </div>
              </div>
            </div>

            {/* Source Items */}
            <div className="divide-y divide-gray-200">
              {items.map((source, idx) => (
                <div key={idx} className="p-4 hover:bg-gray-50 transition-colors">
                  <button
                    onClick={() =>
                      setExpandedIndex(expandedIndex === idx ? null : idx)
                    }
                    className="w-full text-left flex items-center justify-between gap-3 group"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {source.ticker}
                        </span>
                        <span className="text-sm text-gray-600">
                          {source.year}
                        </span>
                        {source.section && (
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                            {source.section}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {source.doc_type === "structured_metric"
                          ? "Financial data point"
                          : "Narrative excerpt"}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {source.similarity_score && (
                        <span className="text-xs font-medium text-gray-600">
                          {(source.similarity_score * 100).toFixed(0)}%
                        </span>
                      )}
                      <ChevronDown
                        className={`w-4 h-4 text-gray-400 transition-transform ${
                          expandedIndex === idx ? "rotate-180" : ""
                        }`}
                      />
                    </div>
                  </button>

                  {/* Expanded Details */}
                  {expandedIndex === idx && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-600">Ticker:</span>
                          <p className="font-medium text-gray-900">
                            {source.ticker}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-600">Year:</span>
                          <p className="font-medium text-gray-900">
                            {source.year}
                          </p>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-600">Type:</span>
                          <p className="font-medium text-gray-900 capitalize">
                            {source.doc_type}
                          </p>
                        </div>
                        {source.section && (
                          <div className="col-span-2">
                            <span className="text-gray-600">Section:</span>
                            <p className="font-medium text-gray-900">
                              {source.section}
                            </p>
                          </div>
                        )}
                        {source.similarity_score && (
                          <div className="col-span-2">
                            <span className="text-gray-600">
                              Relevance Score:
                            </span>
                            <div className="flex items-center gap-2 mt-1">
                              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-green-500"
                                  style={{
                                    width: `${source.similarity_score * 100}%`,
                                  }}
                                />
                              </div>
                              <span className="text-sm font-medium text-gray-900">
                                {(source.similarity_score * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {sources.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No sources available</p>
        </div>
      )}
    </div>
  );
};
