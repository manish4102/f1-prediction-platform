import type { PredictionResponse } from "@/lib/api/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getNextRacePrediction(): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE}/api/predictions/next-race`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to load next-race prediction.");
  }
  return response.json() as Promise<PredictionResponse>;
}

