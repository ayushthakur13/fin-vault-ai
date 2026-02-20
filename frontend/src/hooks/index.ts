"use client";

import React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { queryFinancialData, healthCheck } from "@/lib/api";
import { QueryRequest } from "@/types";

export const useQueryFinancialData = () => {
  return useMutation({
    mutationFn: (request: QueryRequest) => queryFinancialData(request),
  });
};

export const useHealthCheck = () => {
  return useQuery({
    queryKey: ["health"],
    queryFn: healthCheck,
    retry: 2,
    staleTime: 30000,
  });
};

/**
 * Hook for managing query history
 */
export const useQueryHistory = () => {
  const [history, setHistory] = React.useState<
    Array<{ id: string; query: string; timestamp: Date }>
  >(() => {
    if (typeof window === "undefined") return [];
    const stored = localStorage.getItem("query_history");
    return stored ? JSON.parse(stored) : [];
  });

  const addToHistory = React.useCallback(
    (query: string) => {
      const newItem = {
        id: Date.now().toString(),
        query,
        timestamp: new Date(),
      };
      const updated = [newItem, ...history].slice(0, 20);
      setHistory(updated);
      localStorage.setItem("query_history", JSON.stringify(updated));
    },
    [history]
  );

  const clearHistory = React.useCallback(() => {
    setHistory([]);
    localStorage.removeItem("query_history");
  }, []);

  return { history, addToHistory, clearHistory };
};

/**
 * Hook for memory preferences
 */
export const useMemoryPreferences = () => {
  const [preferences, setPreferences] = React.useState(
    () => {
      if (typeof window === "undefined") {
        return {
          risk_tolerance: "moderate",
          focus_sectors: [],
          key_metrics: [],
          save_queries: true,
          max_history: 20,
        };
      }
      const stored = localStorage.getItem("memory_preferences");
      return stored
        ? JSON.parse(stored)
        : {
            risk_tolerance: "moderate",
            focus_sectors: [],
            key_metrics: [],
            save_queries: true,
            max_history: 20,
          };
    }
  );

  const updatePreferences = React.useCallback(
    (updates: Partial<typeof preferences>) => {
      const updated = { ...preferences, ...updates };
      setPreferences(updated);
      localStorage.setItem("memory_preferences", JSON.stringify(updated));
    },
    [preferences]
  );

  return { preferences, updatePreferences };
};
