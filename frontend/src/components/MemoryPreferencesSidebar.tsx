/**
 * Memory Preferences Sidebar
 * Manages user preferences and analysis filters
 */

"use client";

import React, { useState } from "react";
import { Settings } from "lucide-react";

interface MemoryPreferencesSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MemoryPreferencesSidebar: React.FC<
  MemoryPreferencesSidebarProps
> = ({ isOpen, onClose }) => {
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [focusSectors, setFocusSectors] = useState<string[]>([]);
  const [keyMetrics, setKeyMetrics] = useState<string[]>([]);
  const [saveQueries, setSaveQueries] = useState(true);

  const sectors = [
    "Technology",
    "Healthcare",
    "Finance",
    "Energy",
    "Retail",
    "Consumer",
  ];
  const metrics = [
    "Revenue",
    "Profit Margin",
    "ROE",
    "Growth Rate",
    "Debt Ratio",
    "EPS",
  ];

  const toggleFocusSector = (sector: string) => {
    setFocusSectors((prev) =>
      prev.includes(sector)
        ? prev.filter((s) => s !== sector)
        : [...prev, sector]
    );
  };

  const toggleKeyMetric = (metric: string) => {
    setKeyMetrics((prev) =>
      prev.includes(metric)
        ? prev.filter((m) => m !== metric)
        : [...prev, metric]
    );
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed right-0 top-0 h-screen w-80 bg-white border-l border-gray-200 shadow-xl transform transition-transform duration-300 z-50 overflow-y-auto ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Memory
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
            >
              ×
            </button>
          </div>

          {/* Risk Tolerance */}
          <div className="mb-6">
            <label className="text-sm font-semibold text-gray-900 block mb-3">
              Risk Tolerance
            </label>
            <div className="space-y-2">
              {["conservative", "moderate", "aggressive"].map((level) => (
                <label key={level} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    value={level}
                    checked={riskTolerance === level}
                    onChange={(e) => setRiskTolerance(e.target.value)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm text-gray-700 capitalize">{level}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Focus Sectors */}
          <div className="mb-6">
            <label className="text-sm font-semibold text-gray-900 block mb-3">
              Focus Sectors
            </label>
            <div className="space-y-2">
              {sectors.map((sector) => (
                <label key={sector} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={focusSectors.includes(sector)}
                    onChange={() => toggleFocusSector(sector)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm text-gray-700">{sector}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Key Metrics */}
          <div className="mb-6">
            <label className="text-sm font-semibold text-gray-900 block mb-3">
              Key Metrics
            </label>
            <div className="space-y-2">
              {metrics.map((metric) => (
                <label key={metric} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={keyMetrics.includes(metric)}
                    onChange={() => toggleKeyMetric(metric)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm text-gray-700">{metric}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Save Queries */}
          <div className="mb-6">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={saveQueries}
                onChange={(e) => setSaveQueries(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <span className="text-sm text-gray-700">Save queries to history</span>
            </label>
          </div>

          {/* Save Button */}
          <button
            onClick={onClose}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium transition-colors"
          >
            Save Preferences
          </button>
        </div>
      </div>
    </>
  );
};
