import {
  type DynamicStats,
  type OpenPosition,
  type PositionEventItem,
  type PositionEventPayload,
  type SnapshotSummary,
} from "@/types/stats";

export type {
  DynamicStats,
  OpenPosition,
  PositionEventItem,
  PositionEventPayload,
  SnapshotSummary,
} from "@/types/stats";

const API_BASE =
  process.env.NEXT_PUBLIC_STATS_API_URL ?? "http://localhost:8006";

export async function fetchDynamicStats(): Promise<DynamicStats> {
  const res = await fetch(`${API_BASE}/stats/dynamic`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch dynamic stats");
  return (await res.json()) as DynamicStats;
}

export async function fetchOpenPositions(): Promise<OpenPosition[]> {
  const res = await fetch(`${API_BASE}/positions/open`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch open positions");
  return (await res.json()) as OpenPosition[];
}

export async function fetchSnapshotList(limit = 60): Promise<SnapshotSummary[]> {
  const res = await fetch(
    `${API_BASE}/stats/static/list?limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error("Failed to fetch snapshot list");
  return (await res.json()) as SnapshotSummary[];
}

export async function fetchRecentEvents(limit = 50): Promise<PositionEventItem[]> {
  const res = await fetch(`${API_BASE}/events/recent?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch recent events");
  return (await res.json()) as PositionEventItem[];
}


