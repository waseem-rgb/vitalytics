import axios from "axios";
import type { AnalysisResult, UploadResponse } from "./types";

const API_BASE = "";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

export async function runAnalysis(body: {
  patient: { age: number; sex: string; name?: string };
  lab_results: Record<string, number>;
  previous_results?: Record<string, number>;
  use_rag?: boolean;
}): Promise<AnalysisResult> {
  const { data } = await api.post("/api/v1/analyze", body);
  return data;
}

export async function getAnalysis(id: string): Promise<AnalysisResult> {
  const { data } = await api.get(`/api/v1/analysis/${id}`);
  return data;
}

export async function getAnalyses(): Promise<AnalysisResult[]> {
  const { data } = await api.get("/api/v1/analyses");
  return data;
}

export async function getReferenceRanges(): Promise<Record<string, any>> {
  const { data } = await api.get("/api/v1/reference/ranges");
  return data;
}

export async function getPanels(): Promise<Record<string, any[]>> {
  const { data } = await api.get("/api/v1/reference/panels");
  return data;
}

export async function uploadLabReport(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/v1/upload/parse", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function downloadReport(analysisId: string): Promise<Blob> {
  const { data } = await api.get(`/api/v1/reports/${analysisId}/pdf`, {
    responseType: "blob",
  });
  return data;
}

export async function checkHealth(): Promise<{ status: string; rag_ready: boolean }> {
  const { data } = await api.get("/health");
  return data;
}

export async function getRagStatus(): Promise<{
  ingested: boolean;
  total_chunks: number;
  collection_name: string;
  embedding_model: string;
  api_key_set: boolean;
}> {
  const { data } = await api.get("/api/v1/rag/status");
  return data;
}