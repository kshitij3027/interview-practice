import type { Incident, IncidentSummary, Severity } from "../shared/types.js";
import { DataStore } from "./dataStore.js";

const severityOrder: Record<Severity, number> = { sev1: 0, sev2: 1, sev3: 2 };
const priorityOrder = { p0: 0, p1: 1, p2: 2 } as const;

function sortActions(incident: Incident): Incident {
  incident.actionItems.sort((a, b) => {
    const priority = priorityOrder[a.priority] - priorityOrder[b.priority];
    if (priority !== 0) return priority;
    if (a.dueAt === null && b.dueAt !== null) return 1;
    if (a.dueAt !== null && b.dueAt === null) return -1;
    if (a.dueAt !== b.dueAt) return (a.dueAt ?? "").localeCompare(b.dueAt ?? "");
    return a.id.localeCompare(b.id);
  });
  return incident;
}

export class IncidentService {
  constructor(private readonly store: DataStore) {}

  list(severity?: Severity): { incidents: IncidentSummary[]; datasetRevision: number } {
    const incidents = this.store
      .listIncidents()
      .filter((incident) => !severity || incident.severity === severity)
      .sort((a, b) => {
        const sev = severityOrder[a.severity] - severityOrder[b.severity];
        if (sev !== 0) return sev;
        return b.startedAt.localeCompare(a.startedAt) || a.id.localeCompare(b.id);
      })
      .map((incident) => ({
        id: incident.id,
        title: incident.title,
        severity: incident.severity,
        status: incident.status,
        startedAt: incident.startedAt,
        openActionCount: incident.actionItems.filter((item) => item.status === "open").length,
        revision: incident.revision
      }));

    return { incidents, datasetRevision: this.store.getDatasetRevision() };
  }

  detail(id: string): { incident: Incident; datasetRevision: number } | null {
    const incident = this.store.getIncident(id);
    if (!incident) return null;
    return { incident: sortActions(incident), datasetRevision: this.store.getDatasetRevision() };
  }

  setSeverity(id: string, severity: Severity, expectedRevision: number) {
    return {
      incident: sortActions(this.store.updateSeverity(id, severity, expectedRevision)),
      datasetRevision: this.store.getDatasetRevision()
    };
  }
}
