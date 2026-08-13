import cors from "cors";
import express from "express";
import { assignJob, listJobs } from "./store.js";

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

  return app;
}
