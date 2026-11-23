"""POST-PRACTICE ONLY: evaluator checks. Not part of candidate materials."""
import random
import unittest
from pathlib import Path

from coverguard import CoverageAudit, Snapshot, load_snapshot

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'fixtures'


def oracle(snapshot, scope, start, end, required):
    points = {start, end}
    for probe, a, b in snapshot.active.values():
        if snapshot.probes[probe][0] != scope:
            continue
        if start < a < end: points.add(a)
        if start < b < end: points.add(b)
    points = sorted(points)
    covered = 0
    gaps = []
    for left, right in zip(points, points[1:]):
        vendors = {snapshot.probes[probe][1] for probe,a,b in snapshot.active.values()
                   if snapshot.probes[probe][0] == scope and a <= left < b}
        if len(vendors) >= required:
            covered += right - left
        elif gaps and gaps[-1][1] == left:
            gaps[-1] = (gaps[-1][0], right)
        else:
            gaps.append((left, right))
    return {"covered_ms": covered,
            "first_gap_ms": gaps[0][0] if gaps else None,
            "longest_gap_ms": max((b-a for a,b in gaps), default=0),
            "gap_count": len(gaps)}


class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load_snapshot(FIX/'scopes.csv', FIX/'probes.csv', FIX/'observations.csv')
        cls.engine = CoverageAudit(cls.snapshot)

    def check(self, scope, start, end, required):
        q = {'audit_id':'hidden', 'scope_id':scope,'from_ms':start,'until_ms':end,'min_vendors':required}
        actual = self.engine.evaluate(q)
        expected = {'audit_id':'hidden','status':'ok',**oracle(self.snapshot,scope,start,end,required)}
        self.assertEqual(actual, expected)

    def test_overlap_from_same_vendor_is_not_independent(self):
        for k in range(1,5): self.check('EAST', 0, 20, k)

    def test_half_open_boundaries_and_simultaneous_events(self):
        for a,b in ((0,2),(2,5),(5,9),(9,10),(10,12),(15,16),(19,20),(20,21)):
            self.check('EAST',a,b,2)

    def test_retraction_and_latest_corrected_probe(self):
        for k in range(1,4): self.check('COLD', 100, 140, k)
        self.check('WEST', 20, 32, 1)

    def test_gap_clipping_and_contiguity(self):
        for a,b in ((23,27),(24,35),(31,40),(40,50),(47,48),(20,28)):
            for k in (1,2,3): self.check('EAST',a,b,k)

    def test_idle_scope_and_sparse_extremes(self):
        for scope in ('EAST','WEST','LEGACY'):
            for k in (1,4):
                self.check(scope,0,10**12,k)
                self.check(scope,10**12-1,10**12,k)

    def test_order_and_query_independence(self):
        for n in range(60):
            random.seed(n)
            start = random.randint(0,55)
            end = start + random.randint(1,80)
            self.check(random.choice(['EAST','WEST','COLD','LEGACY']),start,end,random.randint(1,4))

    def test_hand_constructed_touching_windows(self):
        snapshot = Snapshot({'X':'x'}, {'p1':('X','A'),'p2':('X','A'),'p3':('X','B')},
                            {'a':('p1',0,4),'b':('p2',4,8),'c':('p3',2,6)})
        engine = CoverageAudit(snapshot)
        q={'audit_id':'edge','scope_id':'X','from_ms':0,'until_ms':8,'min_vendors':2}
        self.assertEqual(engine.evaluate(q), {'audit_id':'edge','status':'ok',
                         **oracle(snapshot,'X',0,8,2)})


if __name__ == '__main__':
    unittest.main()
