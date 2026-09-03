import test from "node:test";
import assert from "node:assert/strict";
import { DataStore } from "../src/server/dataStore.js";

test("store loads independent fixture state", () => {
  const store = new DataStore();
  const incident = store.getIncident("inc-2401");
  assert.equal(incident?.severity, "sev1");
  incident!.severity = "sev3";
  assert.equal(store.getIncident("inc-2401")?.severity, "sev1");
});

test("severity update rejects stale revision without mutation", () => {
  const store = new DataStore();
  assert.throws(() => store.updateSeverity("inc-2401", "sev2", 5), /STALE_REVISION/);
  assert.equal(store.getIncident("inc-2401")?.severity, "sev1");
  assert.equal(store.getDatasetRevision(), 17);
});
