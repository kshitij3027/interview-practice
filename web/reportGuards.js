// Pure decisions for reconciling funnel responses that may arrive out of order.
//
// These live apart from app.js so they can be unit-tested: they touch no DOM and no fetch,
// which is the only way to cover this logic in a dependency-free repo with no jsdom.
//
// The ordering trap worth naming: classifyReport must be called BEFORE the response's
// revision is folded into the client's known revision. Fold first and the condition
// `responseRevision < knownRevision` becomes unsatisfiable, so the staleness guard silently
// disables itself while every other test still passes.

// Monotonic: the client's known revision must never move backwards, or a slow older response
// could make newer state look stale.
export function nextRevision(known, incoming) {
  const current = Number.isFinite(known) ? known : 0;
  if (!Number.isFinite(incoming)) return current;
  return Math.max(current, incoming);
}

// 'apply'   — newest request, right segment, not behind the dataset we already know about
// 'discard' — superseded; some other request owns the UI
// 'refetch' — the dataset moved while this was in flight, so ask again rather than render it
export function classifyReport({
  requestId,
  latestRequestId,
  responseSegment,
  selectedSegment,
  responseRevision,
  knownRevision
}) {
  // 1. Client bookkeeping: a newer request has been issued, so this response is superseded
  //    whatever it contains.
  if (requestId !== latestRequestId) return 'discard';

  // 2. Server-reported truth: the echoed segment is not the one on screen. Redundant with (1)
  //    in the ordinary case, deliberately: a bug in the request counter must not be able to
  //    render one segment's numbers under another segment's label.
  if (responseSegment !== selectedSegment) return 'discard';

  // 3. Computed before an exclusion landed. Discarding alone would leave stale numbers on
  //    screen, so re-request instead.
  if (responseRevision < knownRevision) return 'refetch';

  return 'apply';
}
