import { useEffect, useState } from "react";
import { assignJob, fetchJobs } from "./api";
import type { DeliveryJob } from "./types";
import "./styles.css";

export default function App() {
  const [jobs, setJobs] = useState<DeliveryJob[]>([]);
  const [driver, setDriver] = useState("Taylor");
  const [message, setMessage] = useState("");

  async function loadJobs() {
    try {
      setJobs(await fetchJobs());
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to load jobs");
    }
  }

  useEffect(() => {
    void loadJobs();
  }, []);

  async function onAssign(jobId: string) {
    try {
      const updated = await assignJob(jobId, driver);
      setJobs((current) => current.map((job) => (job.id === updated.id ? updated : job)));
      setMessage(`Assigned ${updated.id} to ${updated.assignedTo}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Assignment failed");
    }
  }

  return (
    <main className="shell">
      <header>
        <div>
          <p className="eyebrow">Operations</p>
          <h1>Dispatch Desk</h1>
        </div>
        <label>
          Dispatcher
          <input value={driver} onChange={(event) => setDriver(event.target.value)} />
        </label>
      </header>

      {message && <p className="message">{message}</p>}

      <section className="grid">
        {jobs.map((job) => (
          <article className="card" key={job.id}>
            <div className="row">
              <strong>{job.customer}</strong>
              <span className={`status ${job.status}`}>{job.status}</span>
            </div>
            <p>{job.address}</p>
            <p className="meta">Priority {job.priority} · {new Date(job.createdAt).toLocaleTimeString()}</p>
            {job.status === "assigned" ? (
              <p className="assigned">Assigned to {job.assignedTo}</p>
            ) : (
              <button onClick={() => void onAssign(job.id)}>Assign to {driver || "dispatcher"}</button>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
