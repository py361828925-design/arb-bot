const API_BASE =
  process.env.NEXT_PUBLIC_STATS_API_URL ?? "http://localhost:8006";

export async function fetchDynamicStats() {
  const res = await fetch(`${API_BASE}/stats/dynamic`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch dynamic stats");
  return res.json();
}

export async function fetchOpenPositions() {
  const res = await fetch(`${API_BASE}/positions/open`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch open positions");
  return res.json();
}

export async function fetchSnapshotList(limit = 60) {
  const res = await fetch(
    `${API_BASE}/stats/static/list?limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error("Failed to fetch snapshot list");
  return res.json();
}

export async function fetchRecentEvents(limit = 50) {
  const res = await fetch(`${API_BASE}/events/recent?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch recent events");
  return res.json();
}


