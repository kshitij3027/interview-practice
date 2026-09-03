import test from "node:test";
import assert from "node:assert/strict";
import { DataStore } from "../src/server/dataStore.js";
import { IncidentService } from "../src/server/incidentService.js";

test("successful severity change increments incident and dataset revisions once", () => {
  const service = new IncidentService(new DataStore());
  const result = service.setSeverity("inc-2398", "sev1", 4);
  assert.equal(result.incident.severity, "sev1");
  assert.equal(result.incident.revision, 5);
  assert.equal(result.datasetRevision, 18);
});
