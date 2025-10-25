import type {
  DynamicStats,
  OpenPosition,
  PositionEventItem,
  SnapshotSummary,
} from "@/types/stats";

export type {
  DynamicStats,
  OpenPosition,
  PositionEventItem,
  SnapshotSummary,
  PositionEventPayload,
} from "@/types/stats";

const resolveApiBase = (): string => {
  if (process.env.NEXT_PUBLIC_STATS_API_URL) {
    return process.env.NEXT_PUBLIC_STATS_API_URL;
  }

  if (typeof window !== "undefined") {
    console.debug("statsApi resolve", window.location.hostname);
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8006`;
  }

  return "http://127.0.0.1:8006";
};

export async function fetchDynamicStats(): Promise<DynamicStats> {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}/stats/dynamic`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch dynamic stats");
  return (await res.json()) as DynamicStats;
}

export async function fetchOpenPositions(): Promise<OpenPosition[]> {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}/positions/open`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch open positions");
  return (await res.json()) as OpenPosition[];
}

export async function fetchSnapshotList(limit = 60): Promise<SnapshotSummary[]> {
  const apiBase = resolveApiBase();
  const res = await fetch(
    `${apiBase}/stats/static/list?limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error("Failed to fetch snapshot list");
  return (await res.json()) as SnapshotSummary[];
}

export async function fetchRecentEvents(limit = 50): Promise<PositionEventItem[]> {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}/events/recent?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch recent events");
  return (await res.json()) as PositionEventItem[];
}


