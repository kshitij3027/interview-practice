import type { DeliveryJob } from "./types";

const API_BASE = "http://localhost:3001/api";

export async function fetchJobs(): Promise<DeliveryJob[]> {
  const response = await fetch(`${API_BASE}/jobs`);
  if (!response.ok) throw new Error("Failed to load jobs");
  const data = await response.json();
  return data.jobs;
}

export async function assignJob(jobId: string, driver: string): Promise<DeliveryJob> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/assign`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ driver })
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data.error ?? "Failed to assign job");
  return data.job;
}
