import type { PredictionResponse } from "@/lib/api/types";

function resolveApiBase() {
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }

  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}/_/backend`;
  }

  return "http://localhost:8000";
}

const API_BASE = resolveApiBase();

export async function getNextRacePrediction(): Promise<PredictionResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/api/predictions/next-race`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });

    if (!response.ok) {
      throw new Error("Failed to load next-race prediction.");
    }

    return response.json() as Promise<PredictionResponse>;
  } catch {
    return null;
  }
}
