import request from "supertest";
import { beforeEach, describe, expect, it } from "vitest";
import { createApp } from "../src/app.js";
import { resetStore } from "../src/store.js";

const app = createApp();

beforeEach(() => {
  resetStore();
});

describe("existing job API", () => {
  it("lists the seeded jobs", async () => {
    const response = await request(app).get("/api/jobs");
    expect(response.status).toBe(200);
    expect(response.body.jobs).toHaveLength(4);
  });

  it("manually assigns a queued job", async () => {
    const response = await request(app)
      .patch("/api/jobs/job-101/assign")
      .send({ driver: "Jordan" });

    expect(response.status).toBe(200);
    expect(response.body.job.status).toBe("assigned");
    expect(response.body.job.assignedTo).toBe("Jordan");
  });

  it("rejects a blank driver name", async () => {
    const response = await request(app)
      .patch("/api/jobs/job-101/assign")
      .send({ driver: "   " });

    expect(response.status).toBe(400);
  });

  it("rejects reassigning an already-assigned job", async () => {
    const response = await request(app)
      .patch("/api/jobs/job-104/assign")
      .send({ driver: "Jordan" });

    expect(response.status).toBe(409);
  });
});

describe("claim next job", () => {
  it("claims the highest-priority queued job, earliest createdAt breaking ties", async () => {
    const response = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "Jordan", idempotencyKey: "key-1" });

    expect(response.status).toBe(200);
    expect(response.body.job.id).toBe("job-102");
    expect(response.body.job.status).toBe("assigned");
    expect(response.body.job.assignedTo).toBe("Jordan");
  });

  it("rejects a blank dispatcher name", async () => {
    const response = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "   ", idempotencyKey: "key-1" });

    expect(response.status).toBe(400);
  });

  it("rejects a missing idempotency key", async () => {
    const response = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "Jordan" });

    expect(response.status).toBe(400);
  });

  it("returns the same claimed job when the same idempotency key is repeated", async () => {
    const first = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "Jordan", idempotencyKey: "key-1" });

    const second = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "Jordan", idempotencyKey: "key-1" });

    expect(second.status).toBe(200);
    expect(second.body.job.id).toBe(first.body.job.id);

    const jobs = await request(app).get("/api/jobs");
    const queuedCount = jobs.body.jobs.filter((job: { status: string }) => job.status === "queued").length;
    expect(queuedCount).toBe(2);
  });

  it("claims a different job for two different idempotency keys", async () => {
    const first = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "Jordan", idempotencyKey: "key-1" });

    const second = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "Riley", idempotencyKey: "key-2" });

    expect(first.body.job.id).not.toBe(second.body.job.id);
  });

  it("returns a distinguishable non-2xx response when no queued jobs remain", async () => {
    await request(app).post("/api/jobs/claim-next").send({ dispatcher: "Jordan", idempotencyKey: "key-1" });
    await request(app).post("/api/jobs/claim-next").send({ dispatcher: "Riley", idempotencyKey: "key-2" });
    await request(app).post("/api/jobs/claim-next").send({ dispatcher: "Sam", idempotencyKey: "key-3" });

    const response = await request(app)
      .post("/api/jobs/claim-next")
      .send({ dispatcher: "Casey", idempotencyKey: "key-4" });

    expect(response.status).toBe(409);
    expect(response.body.error).toBe("no-queued-jobs");
  });
});
