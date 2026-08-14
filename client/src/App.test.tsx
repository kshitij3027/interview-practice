import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";
import type { DeliveryJob } from "./types";

vi.mock("./api");

const queuedJob: DeliveryJob = {
  id: "job-101",
  customer: "Maya Chen",
  address: "18 Market St",
  priority: 2,
  createdAt: "2026-08-13T15:00:00.000Z",
  status: "queued"
};

const claimedJob: DeliveryJob = { ...queuedJob, status: "assigned", assignedTo: "Taylor" };

beforeEach(() => {
  vi.mocked(api.fetchJobs).mockResolvedValue([queuedJob]);
});

describe("Claim next job control", () => {
  it("claims a job and reflects it on the dashboard without a manual refresh", async () => {
    vi.mocked(api.claimNextJob).mockResolvedValue(claimedJob);
    const user = userEvent.setup();

    render(<App />);
    await screen.findByText("Maya Chen");

    await user.click(screen.getByRole("button", { name: "Claim next job" }));

    expect(api.claimNextJob).toHaveBeenCalledTimes(1);
    await screen.findByText("Assigned to Taylor");
    expect(api.fetchJobs).toHaveBeenCalledTimes(1); // no extra reload needed on success
  });

  it("disables the control while a claim is in flight to prevent duplicate submissions", async () => {
    let resolveClaim!: (job: DeliveryJob) => void;
    vi.mocked(api.claimNextJob).mockReturnValue(
      new Promise((resolve) => {
        resolveClaim = resolve;
      })
    );
    const user = userEvent.setup();

    render(<App />);
    await screen.findByText("Maya Chen");

    const button = screen.getByRole("button", { name: "Claim next job" });
    await user.click(button);
    expect(button).toBeDisabled();

    await user.click(button); // second click while in flight should be a no-op
    expect(api.claimNextJob).toHaveBeenCalledTimes(1);

    resolveClaim(claimedJob);
    await waitFor(() => expect(button).not.toBeDisabled());
  });

  it("reconciles the dashboard and shows a message when no jobs remain to claim", async () => {
    vi.mocked(api.claimNextJob).mockRejectedValue(new Error("no-queued-jobs"));
    const user = userEvent.setup();

    render(<App />);
    await screen.findByText("Maya Chen");

    await user.click(screen.getByRole("button", { name: "Claim next job" }));

    await screen.findByText("No queued jobs left to claim.");
    expect(api.fetchJobs).toHaveBeenCalledTimes(2); // initial load + reconciliation reload
  });
});
