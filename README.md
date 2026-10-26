# OpsDispatch — HARD 60-minute AI-assisted customer interview

## Customer / business context

An enterprise incident-response vendor needs to assign newly opened customer incidents to on-call responders for one dispatch window. The intake system has already filtered out unqualified responders and estimated a response time for each allowed incident/responder pairing. Some responders can handle several tickets; however, each on-call pod has an independent ceiling on the total number of tickets accepted by **all** its responders together.

The existing dispatch desk takes the closest available responder for each incident in spreadsheet order. This frequently leaves critical incidents unserved even when a different overall arrangement would cover them. The customer wants a globally defensible plan and a useful account of why a seemingly fast local decision may be wrong.

You choose the technical approach. Deterministic, heuristic, LLM-based or hybrid designs are allowed, provided they meet the exact correctness and performance requirements. No external service, SDK, credentials, or model is needed.

## Supplied data

The checked-in snapshot is intentionally small; all incidents belong to **one** dispatch window.

- **fixtures/pods.csv**: pod_id,max_parallel. A pod can accept at most this many incidents **in total** for the snapshot, even when its responders' individual capacities sum to more. A zero limit is valid.
- **fixtures/responders.csv**: responder_id,pod_id,capacity. Each responder belongs to exactly one pod and may accept at most capacity incidents (zero is valid). A responder's capacity does not transfer to another responder.
- **fixtures/incidents.csv**: incident_id,severity. Severity is sev0 (most critical), sev1, or sev2. Every incident needs **one distinct responder** to be covered; partial coverage is not useful.
- **fixtures/routes.csv**: incident_id,responder_id,eta_minutes. Each row means this responder is eligible for that incident, with the given estimated response time. No listed row means the pairing is forbidden, regardless of how close the responder appears. Travel estimates are nonnegative whole minutes. A responder may appear on many route rows, but its capacity still applies.

The supplied records.py loader validates these files and returns a Snapshot containing immutable Pod, Responder, Incident, and Route records. It deduplicates **identical replays** of an ID or incident/responder route pair. Reusing an ID/pair with different values is a fatal input error. References to unknown pods/responders/incidents are invalid. IDs are case-sensitive ASCII letters/digits/_/- (1–48 characters). Numeric CSV fields are canonical unsigned decimals, with no leading zeros; pod limits are 0–20, responder capacities 0–8, and ETAs 0–240.

## Primary customer problem

Implement plan(snapshot) in assignment.py and any supporting code so the command below outputs **one complete dispatch plan**. Each incident may be covered at most once and only by a listed eligible responder. Respect **both** individual responder capacities and overall pod ceilings. Leaving an incident unassigned is allowed if necessary.

Among all feasible dispatch plans, choose the best under this **strict objective order**:

1. Cover as many sev0 incidents as possible.
2. Among plans meeting #1, cover as many sev1 incidents as possible.
3. Among plans meeting #1–2, cover as many sev2 incidents as possible.
4. Among plans meeting #1–3, minimize the **sum of eta_minutes for assigned pairs**.

These priorities are lexicographic, not a weighted average specified by the customer. For example, serving one additional sev0 incident is always preferable to covering any number of sev1/sev2 incidents or saving any amount of response time. Simply selecting the shortest ETA for each incident in isolation will not necessarily produce a correct global plan.

For equally optimal plans under all four criteria, **any** is acceptable, but the selected plan must be reproducible across runs and invariant to permutations of equivalent input rows. Return assignments sorted by incident_id (case-sensitive) and then responder_id.

## Expected deliverable / output contract

On a valid snapshot, emit exactly one compact JSON object to stdout, with exactly these top-level keys:

~~~json
{"status":"planned","assignment_count":1,"by_severity":{"sev0":1,"sev1":0,"sev2":0},"total_eta_minutes":6,"assignments":[{"incident_id":"EXAMPLE","responder_id":"R-1","eta_minutes":6}]}
~~~

The example shows the **shape only**, not an answer for the provided fixtures.

- assignment_count equals the number of distinct covered incidents and the sum of by_severity values.
- total_eta_minutes is the exact integer sum of selected route ETAs; do not count any unassigned incident.
- Every entry in assignments must correspond to an existing route and contain exactly the keys shown. No duplicate incident IDs may occur.
- An empty feasible plan must have zero counts, zero total ETA, and an empty assignments array.
- Invalid snapshot data must stop **before** emitting a plan; use nonzero exit status and send a useful error to stderr. The supplied loader/CLI already handles this.
- The --check-inputs flag validates the snapshot and prints its record counts, without running your planner. It is not a correctness oracle for the assignment.

## Important correctness cases

Think through scarcity across incident severities; a responder who is the only possible choice for one incident; multiple responders sharing a smaller pod ceiling; a responder with spare personal capacity while its pod is full; zero-capacity pods/responders; routes with equal or zero ETA; duplicate delivery of identical route rows; an incident with no eligible route; and plans with identical objective values that must behave consistently when source rows are shuffled. Your implementation should derive additional tests that exercise these cases rather than trusting the fixture's apparent answer.

## Production constraints

The intended production batch has approximately **15,000 incidents, 4,000 responders, 350 pods, and 250,000 distinct eligible routes**. The incident mix may be heavily skewed toward a single pod, and not all incidents are coverable. The budget is approximately **768 MB resident memory** with a **60-second batch processing target** on an 8-core host, excluding CSV parsing. A solution that checks or enumerates all combinations of assignments cannot satisfy the customer's needs. Explain the expected scaling of your approach, even if you implement a narrower but correct version during the hour.

## In scope / out of scope

In scope: one immutable CSV snapshot, exact coverage priorities, globally best ETA subject to those priorities, both capacity limits, stable output, and focused verification. You can change/add Python modules and tests.

Out of scope: real-time arrival of incidents during dispatch, calendar availability, continuous routing updates, authentication, remote APIs, UI, billing, and persistence. Route eligibility and ETA estimates are already provided; **do not invent or call a geocoding service**.

## Setup and verification

Requires Python 3.11+ and its standard library, no third-party packages.

~~~bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 dispatch.py --check-inputs
python3 dispatch.py
~~~

You may specify alternate file paths with --pods, --responders, --incidents, and --routes. The starter's plan function deliberately returns status "not_implemented"; the baseline tests check fixture parsing and executable wiring, **not** the target planning behavior. After implementing the plan, add focused tests for your own claims of correctness and performance.

## 60-minute interview instruction

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or any tools you would use on the job. Start by inspecting the data, constraints, and supplied contracts. Explain how you intend to select the globally best feasible plan, where the obvious shortcuts fail, and how you verify the result. Prioritize a credible, tested implementation and be prepared to defend correctness, scaling, and design alternatives during the walkthrough.
