export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function json(res) {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  scenarios: () => fetch(`${API_BASE}/scenarios`).then(json),
  stats: () => fetch(`${API_BASE}/stats`).then(json),
  audit: (limit = 300) => fetch(`${API_BASE}/audit?limit=${limit}`).then(json),
  rules: () => fetch(`${API_BASE}/rules`).then(json),
  evalsList: () => fetch(`${API_BASE}/evals`).then(json),
  evalDetail: (name) => fetch(`${API_BASE}/evals/${name}`).then(json),
  status: () => fetch(`${API_BASE}/runs/status`).then(json),
  start: (body) =>
    fetch(`${API_BASE}/runs/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(json),
  stop: () => fetch(`${API_BASE}/runs/stop`, { method: "POST" }).then(json),
};
