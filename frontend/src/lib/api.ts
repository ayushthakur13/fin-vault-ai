/**
 * API Client for FinVault AI Backend
 */

import axios, { AxiosError } from "axios";
import { QueryRequest, QueryResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface ApiError {
  message: string;
  status?: number;
  details?: string;
}

export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    return {
      message: axiosError.response?.data
        ? typeof axiosError.response.data === "string"
          ? axiosError.response.data
          : (axiosError.response.data as any).detail ||
            (axiosError.response.data as any).message ||
            "Request failed"
        : error.message || "Unknown error",
      status: axiosError.status,
      details: JSON.stringify(axiosError.response?.data),
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      details: error.stack,
    };
  }

  return {
    message: "An unexpected error occurred",
  };
};

/**
 * Query financial data from backend
 */
export const queryFinancialData = async (
  request: QueryRequest
): Promise<QueryResponse> => {
  try {
    const response = await apiClient.post<QueryResponse>("/query", request);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Health check endpoint
 */
export const healthCheck = async (): Promise<{ status: string }> => {
  try {
    const response = await apiClient.get<{ status: string }>("/health");
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export default apiClient;
