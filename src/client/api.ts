import type { IncidentDetailResponse, IncidentListResponse, Severity } from "../shared/types.js";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const body = await response.json();
  if (!response.ok) throw Object.assign(new Error(body.error ?? "request_failed"), { status: response.status, body });
  return body as T;
}

export function fetchIncidents(severity: Severity | "all"): Promise<IncidentListResponse> {
  const query = severity === "all" ? "" : `?severity=${encodeURIComponent(severity)}`;
  return request(`/api/incidents${query}`);
}

export function fetchIncident(id: string): Promise<IncidentDetailResponse> {
  return request(`/api/incidents/${encodeURIComponent(id)}`);
}

export function updateSeverity(id: string, severity: Severity, expectedRevision: number): Promise<IncidentDetailResponse> {
  return request(`/api/incidents/${encodeURIComponent(id)}/severity`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ severity, expectedRevision })
  });
}
