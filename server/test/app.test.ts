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
