import type {
  ConfigResponse,
  ConfigUpdatePayload,
} from "@/types/config";

export type { ConfigResponse, ConfigUpdatePayload, RiskLimits, Thresholds } from "@/types/config";

const resolveApiBase = (): string => {
  if (process.env.NEXT_PUBLIC_CONFIG_API_URL) {
    return process.env.NEXT_PUBLIC_CONFIG_API_URL;
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8003`;
  }

  return "http://127.0.0.1:8003";
};

export async function fetchConfig(): Promise<ConfigResponse> {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}/config/current`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch config");
  return (await res.json()) as ConfigResponse;
}

export async function updateConfig(payload: ConfigUpdatePayload): Promise<ConfigResponse> {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}/config/current`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update config");
  return (await res.json()) as ConfigResponse;
}
