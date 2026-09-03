import type { Incident, IncidentSummary, Severity } from "../shared/types.js";

export interface AppState {
  severity: Severity | "all";
  incidents: IncidentSummary[];
  selectedIncidentId: string | null;
  selectedIncident: Incident | null;
  datasetRevision: number;
  loadingList: boolean;
  loadingDetail: boolean;
  savingSeverity: boolean;
  error: string | null;
}

export const state: AppState = {
  severity: "all",
  incidents: [],
  selectedIncidentId: null,
  selectedIncident: null,
  datasetRevision: 0,
  loadingList: false,
  loadingDetail: false,
  savingSeverity: false,
  error: null
};
