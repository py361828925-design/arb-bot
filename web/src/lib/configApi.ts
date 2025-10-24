import {
  type ConfigResponse,
  type ConfigUpdatePayload,
  type RiskLimits,
  type Thresholds,
} from "@/types/config";

export type { ConfigResponse, ConfigUpdatePayload, RiskLimits, Thresholds } from "@/types/config";

const API_BASE =
  process.env.NEXT_PUBLIC_CONFIG_API_URL ?? "http://localhost:8003";

export async function fetchConfig(): Promise<ConfigResponse> {
  const res = await fetch(`${API_BASE}/config/current`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch config");
  return (await res.json()) as ConfigResponse;
}

export async function updateConfig(payload: ConfigUpdatePayload): Promise<ConfigResponse> {
  const res = await fetch(`${API_BASE}/config/current`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update config");
  return (await res.json()) as ConfigResponse;
}
