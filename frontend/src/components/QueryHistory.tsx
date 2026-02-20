/**
 * Query History Component
 * Displays previous queries with timestamps
 */

"use client";

import React from "react";
import { Clock, Trash2, Copy } from "lucide-react";

interface QueryHistoryItem {
  id: string;
  query: string;
  mode: "quick" | "deep";
  timestamp: Date;
  retrievalMode?: string;
}

interface QueryHistoryProps {
  items: QueryHistoryItem[];
  onSelect: (query: string) => void;
  onClear: () => void;
}

export const QueryHistory: React.FC<QueryHistoryProps> = ({
  items,
  onSelect,
  onClear,
}) => {
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return new Date(date).toLocaleDateString();
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Query History
        </h2>
        {items.length > 0 && (
          <button
            onClick={onClear}
            className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="text-center text-gray-500 py-8">No query history yet</p>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelect(item.query)}
              className="w-full text-left p-3 rounded-lg hover:bg-gray-50 border border-gray-200 transition-colors group"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 truncate font-medium">
                    {item.query}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`text-xs px-2 py-1 rounded capitalize ${
                        item.mode === "quick"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-purple-100 text-purple-700"
                      }`}
                    >
                      {item.mode}
                    </span>
                    <span className="text-xs text-gray-600">
                      {formatTime(item.timestamp)}
                    </span>
                  </div>
                </div>
                <Copy className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
