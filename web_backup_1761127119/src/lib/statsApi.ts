const resolveApiBase = (): string => {
  if (process.env.NEXT_PUBLIC_STATS_API_URL) {
    return process.env.NEXT_PUBLIC_STATS_API_URL;
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8006`;
  }

  return "http://127.0.0.1:8006";
};

export async function fetchDynamicStats() {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}/stats/dynamic`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch dynamic stats");
  return res.json();
}

export async function fetchOpenPositions() {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}/positions/open`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch open positions");
  return res.json();
}

export async function fetchSnapshotList(limit = 60) {
  const apiBase = resolveApiBase();
  const res = await fetch(
    `${apiBase}/stats/static/list?limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error("Failed to fetch snapshot list");
  return res.json();
}
