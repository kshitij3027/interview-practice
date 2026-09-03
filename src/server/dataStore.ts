import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Incident, Severity } from "../shared/types.js";

interface FixtureShape {
  datasetRevision: number;
  incidents: Incident[];
}

export class DataStore {
  private incidents: Incident[];
  private datasetRevision: number;

  constructor(fixturePath = join(process.cwd(), "fixtures", "incidents.json")) {
    const raw = JSON.parse(readFileSync(fixturePath, "utf-8")) as FixtureShape;
    this.incidents = structuredClone(raw.incidents);
    this.datasetRevision = raw.datasetRevision;
  }

  getDatasetRevision(): number {
    return this.datasetRevision;
  }

  listIncidents(): Incident[] {
    return structuredClone(this.incidents);
  }

  getIncident(id: string): Incident | null {
    const incident = this.incidents.find((item) => item.id === id);
    return incident ? structuredClone(incident) : null;
  }

  updateSeverity(id: string, severity: Severity, expectedRevision: number): Incident {
    const incident = this.incidents.find((item) => item.id === id);
    if (!incident) throw new Error("NOT_FOUND");
    if (incident.revision !== expectedRevision) throw new Error("STALE_REVISION");
    if (incident.severity === severity) return structuredClone(incident);
    incident.severity = severity;
    incident.revision += 1;
    this.datasetRevision += 1;
    return structuredClone(incident);
  }
}
