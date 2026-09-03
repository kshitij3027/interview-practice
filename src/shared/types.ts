export type Severity = "sev1" | "sev2" | "sev3";
export type IncidentStatus = "active" | "monitoring" | "resolved";
export type ActionPriority = "p0" | "p1" | "p2";
export type ActionStatus = "open" | "done";

export interface ActionItem {
  id: string;
  summary: string;
  owner: string | null;
  priority: ActionPriority;
  dueAt: string | null;
  status: ActionStatus;
  revision: number;
}

export interface Incident {
  id: string;
  title: string;
  severity: Severity;
  status: IncidentStatus;
  startedAt: string;
  responders: string[];
  revision: number;
  actionItems: ActionItem[];
}

export interface IncidentSummary {
  id: string;
  title: string;
  severity: Severity;
  status: IncidentStatus;
  startedAt: string;
  openActionCount: number;
  revision: number;
}

export interface IncidentDetailResponse {
  incident: Incident;
  datasetRevision: number;
}

export interface IncidentListResponse {
  incidents: IncidentSummary[];
  datasetRevision: number;
}
