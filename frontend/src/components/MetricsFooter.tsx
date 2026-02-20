/**
 * Metrics Footer Component
 * Displays performance metrics and resource usage
 */

"use client";

import React from "react";
import { Zap, Gauge, Cpu } from "lucide-react";

interface MetricsFooterProps {
  latencyMs?: number;
  tokensUsed?: number;
  modelUsed?: string;
  retrievalMode?: string;
}

export const MetricsFooter: React.FC<MetricsFooterProps> = ({
  latencyMs = 0,
  tokensUsed = 0,
  modelUsed = "llama-3.1-8b-instant",
  retrievalMode = "hybrid",
}) => {
  // Estimate cost (simplified)
  const estimatedCost = ((tokensUsed || 0) * 0.00002).toFixed(4);

  return (
    <footer className="border-t border-gray-200 bg-gray-50 p-4">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Latency */}
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-blue-600" />
            <div>
              <p className="text-xs text-gray-600">Latency</p>
              <p className="text-sm font-semibold text-gray-900">
                {latencyMs > 0 ? `${latencyMs}ms` : "—"}
              </p>
            </div>
          </div>

          {/* Tokens */}
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-green-600" />
            <div>
              <p className="text-xs text-gray-600">Tokens</p>
              <p className="text-sm font-semibold text-gray-900">
                {tokensUsed > 0 ? tokensUsed.toLocaleString() : "—"}
              </p>
            </div>
          </div>

          {/* Model */}
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-600" />
            <div>
              <p className="text-xs text-gray-600">Model</p>
              <p className="text-sm font-semibold text-gray-900 truncate">
                {modelUsed.replace("llama-", "").replace("-instant", " ↯")}
              </p>
            </div>
          </div>

          {/* Retrieval Mode */}
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-purple-600" />
            <div>
              <p className="text-xs text-gray-600">Retrieval</p>
              <p className="text-sm font-semibold text-gray-900 capitalize">
                {retrievalMode}
              </p>
            </div>
          </div>
        </div>

        {/* Cost Estimate */}
        {tokensUsed > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200 text-right">
            <p className="text-xs text-gray-600">
              Estimated cost: <span className="font-semibold">${estimatedCost}</span>
            </p>
          </div>
        )}
      </div>
    </footer>
  );
};
