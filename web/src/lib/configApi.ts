const API_BASE =
  process.env.NEXT_PUBLIC_CONFIG_API_URL ?? "http://localhost:8003";

export async function fetchConfig() {
  const res = await fetch(`${API_BASE}/config/current`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}

export async function updateConfig(payload: any) {
  const res = await fetch(`${API_BASE}/config/current`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update config");
  return res.json();
}
