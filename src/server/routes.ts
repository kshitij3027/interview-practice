import type { IncomingMessage, ServerResponse } from "node:http";
import type { Severity } from "../shared/types.js";
import { IncidentService } from "./incidentService.js";
import { json, readJson } from "./http.js";

const validSeverities = new Set<Severity>(["sev1", "sev2", "sev3"]);

export async function handleApi(req: IncomingMessage, res: ServerResponse, service: IncidentService): Promise<boolean> {
  const url = new URL(req.url ?? "/", "http://localhost");
  if (!url.pathname.startsWith("/api/")) return false;

  if (req.method === "GET" && url.pathname === "/api/health") {
    json(res, 200, { ok: true });
    return true;
  }

  if (req.method === "GET" && url.pathname === "/api/incidents") {
    const raw = url.searchParams.get("severity");
    const severity = raw && validSeverities.has(raw as Severity) ? (raw as Severity) : undefined;
    json(res, 200, service.list(severity));
    return true;
  }

  const detailMatch = url.pathname.match(/^\/api\/incidents\/([^/]+)$/);
  if (req.method === "GET" && detailMatch) {
    const result = service.detail(decodeURIComponent(detailMatch[1]));
    if (!result) json(res, 404, { error: "incident_not_found" });
    else json(res, 200, result);
    return true;
  }

  const severityMatch = url.pathname.match(/^\/api\/incidents\/([^/]+)\/severity$/);
  if (req.method === "PATCH" && severityMatch) {
    const body = await readJson<{ severity?: string; expectedRevision?: number }>(req);
    if (!body.severity || !validSeverities.has(body.severity as Severity) || !Number.isInteger(body.expectedRevision)) {
      json(res, 400, { error: "invalid_severity_request" });
      return true;
    }
    try {
      json(res, 200, service.setSeverity(decodeURIComponent(severityMatch[1]), body.severity as Severity, body.expectedRevision!));
    } catch (error) {
      if ((error as Error).message === "NOT_FOUND") json(res, 404, { error: "incident_not_found" });
      else if ((error as Error).message === "STALE_REVISION") json(res, 409, { error: "stale_revision", current: service.detail(decodeURIComponent(severityMatch[1])) });
      else throw error;
    }
    return true;
  }

  json(res, 404, { error: "api_route_not_found" });
  return true;
}
