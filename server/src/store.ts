import type { DeliveryJob } from "./types.js";

const initialJobs: DeliveryJob[] = [
  {
    id: "job-101",
    customer: "Maya Chen",
    address: "18 Market St",
    priority: 2,
    createdAt: "2026-08-13T15:00:00.000Z",
    status: "queued"
  },
  {
    id: "job-102",
    customer: "Noah Williams",
    address: "42 Pine Ave",
    priority: 5,
    createdAt: "2026-08-13T14:20:00.000Z",
    status: "queued"
  },
  {
    id: "job-103",
    customer: "Ava Patel",
    address: "7 Mission Rd",
    priority: 5,
    createdAt: "2026-08-13T14:45:00.000Z",
    status: "queued"
  },
  {
    id: "job-104",
    customer: "Liam Brooks",
    address: "91 King St",
    priority: 1,
    createdAt: "2026-08-13T13:15:00.000Z",
    status: "assigned",
    assignedTo: "Riley"
  }
];

let jobs = structuredClone(initialJobs);
let claims = new Map<string, string>();

export function listJobs() {
  return jobs.map((job) => ({ ...job }));
}

export function assignJob(jobId: string, driver: string) {
  const job = jobs.find((candidate) => candidate.id === jobId);
  if (!job) return { kind: "not-found" as const };
  if (job.status === "assigned") return { kind: "already-assigned" as const };

  job.status = "assigned";
  job.assignedTo = driver;
  return { kind: "ok" as const, job: { ...job } };
}

export function claimNextJob(dispatcher: string, idempotencyKey: string) {
  const claimedJobId = claims.get(idempotencyKey);
  if (claimedJobId) {
    const job = jobs.find((candidate) => candidate.id === claimedJobId);
    return { kind: "ok" as const, job: { ...job! } };
  }

  const nextJob = jobs
    .filter((job) => job.status === "queued")
    .sort((a, b) => b.priority - a.priority || a.createdAt.localeCompare(b.createdAt))[0];

  if (!nextJob) return { kind: "no-jobs" as const };

  const result = assignJob(nextJob.id, dispatcher);
  if (result.kind === "ok") claims.set(idempotencyKey, nextJob.id);
  return result;
}

export function resetStore() {
  jobs = structuredClone(initialJobs);
  claims = new Map();
}
