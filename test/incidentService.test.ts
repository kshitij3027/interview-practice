import test from "node:test";
import assert from "node:assert/strict";
import { DataStore } from "../src/server/dataStore.js";
import { IncidentService } from "../src/server/incidentService.js";

test("list filters severity and derives open action counts", () => {
  const service = new IncidentService(new DataStore());
  const result = service.list("sev2");
  assert.deepEqual(result.incidents.map((item) => item.id), ["inc-2398", "inc-2374"]);
  assert.deepEqual(result.incidents.map((item) => item.openActionCount), [1, 1]);
});

test("detail sorts action items deterministically", () => {
  const service = new IncidentService(new DataStore());
  const detail = service.detail("inc-2401");
  assert.deepEqual(detail?.incident.actionItems.map((item) => item.id), ["act-902", "act-901", "act-903"]);
});
