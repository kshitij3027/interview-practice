import cors from "cors";
import express from "express";
import { assignJob, claimNextJob, listJobs } from "./store.js";

export function createApp() {
  const app = express();
  app.use(cors());
  app.use(express.json());

  app.get("/api/jobs", (_req, res) => {
    res.json({ jobs: listJobs() });
  });

  app.patch("/api/jobs/:jobId/assign", (req, res) => {
    const driver = typeof req.body?.driver === "string" ? req.body.driver.trim() : "";
    if (!driver) {
      return res.status(400).json({ error: "driver is required" });
    }

    const result = assignJob(req.params.jobId, driver);
    if (result.kind === "not-found") {
      return res.status(404).json({ error: "job not found" });
    }
    if (result.kind === "already-assigned") {
      return res.status(409).json({ error: "job already assigned" });
    }

    return res.json({ job: result.job });
  });

  app.post("/api/jobs/claim-next", (req, res) => {
    const dispatcher = typeof req.body?.dispatcher === "string" ? req.body.dispatcher.trim() : "";
    const idempotencyKey = typeof req.body?.idempotencyKey === "string" ? req.body.idempotencyKey.trim() : "";

    if (!dispatcher) {
      return res.status(400).json({ error: "dispatcher is required" });
    }
    if (!idempotencyKey) {
      return res.status(400).json({ error: "idempotencyKey is required" });
    }

    const result = claimNextJob(dispatcher, idempotencyKey);
    if (result.kind === "no-jobs") {
      return res.status(409).json({ error: "no-queued-jobs" });
    }

    return res.json({ job: result.job });
  });

  return app;
}
