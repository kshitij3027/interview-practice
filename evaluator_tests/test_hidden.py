"""POST-PRACTICE ONLY: must remain on evaluator branch."""
from __future__ import annotations

import unittest

from airspace.engine import AirspaceReview
from airspace.io import Query, Zone


def zone(name, outer, holes=(), *, region='west', priority=10, start=0, end=100, low=0, high=1000):
    return Zone(name, region, priority, start, end, low, high, tuple(outer), tuple(tuple(h) for h in holes))


def q(x, y, *, region='west', at=50, altitude=100, limit=10):
    return Query('same-request-id', region, x, y, at, altitude, limit)


SQUARE = ((0,0), (10,0), (10,10), (0,10))
HOLE = ((3,3), (7,3), (7,7), (3,7))


class HiddenGeometryChecks(unittest.TestCase):
    def test_outer_boundaries_are_included(self):
        s = AirspaceReview([zone('z', SQUARE)])
        for xy in [(0,0), (10,10), (0,5), (10,5), (5,0), (5,10), (5,5)]:
            self.assertEqual(s.select(q(*xy)), ['z'], xy)
        self.assertEqual(s.select(q(-1,5)), [])

    def test_hole_and_hole_boundary_are_excluded(self):
        s = AirspaceReview([zone('holed', SQUARE, [HOLE])])
        for xy in [(3,3), (7,5), (5,5), (7,7), (5,3)]:
            self.assertEqual(s.select(q(*xy)), [], xy)
        self.assertEqual(s.select(q(2,5)), ['holed'])

    def test_concave_and_reverse_winding(self):
        shape = ((0,0), (10,0), (10,10), (7,10), (7,3), (0,3))
        s = AirspaceReview([zone('cw', tuple(reversed(shape)))])
        self.assertEqual(s.select(q(8,9)), ['cw'])
        self.assertEqual(s.select(q(2,9)), [])
        self.assertEqual(s.select(q(7,5)), ['cw'])

    def test_exact_diagonal_and_large_negative_coordinates(self):
        s = AirspaceReview([zone('tri', ((-1000000000,0), (1000000000,0), (0,1000000000)))])
        self.assertEqual(s.select(q(-500000000,500000000)), ['tri'])
        self.assertEqual(s.select(q(-500000000,500000001)), [])

    def test_ordering_priority_net_area_and_tied_zone_ids(self):
        small = ((0,0),(4,0),(4,4),(0,4))
        zones = [zone('large', SQUARE), zone('holed', SQUARE, [HOLE]), zone('b', small), zone('a', small), zone('low-priority', small, priority=9)]
        s = AirspaceReview(zones)
        self.assertEqual(s.select(q(0,0)), ['a', 'b', 'holed', 'large', 'low-priority'])
        self.assertEqual(s.select(q(0,0, limit=2)), ['a', 'b'])
        self.assertEqual(AirspaceReview(list(reversed(zones))).select(q(0,0)), ['a','b','holed','large','low-priority'])

    def test_region_time_and_altitude_half_open(self):
        s = AirspaceReview([zone('early', SQUARE, start=0, end=50, low=0, high=100), zone('later', SQUARE, start=50, end=100, low=100, high=200), zone('other-region', SQUARE, region='coast')])
        self.assertEqual(s.select(q(1,1, at=49, altitude=99)), ['early'])
        self.assertEqual(s.select(q(1,1, at=50, altitude=100)), ['later'])
        self.assertEqual(s.select(q(1,1, at=100, altitude=200)), [])
        self.assertEqual(s.select(q(1,1, region='coast')), ['other-region'])
        self.assertEqual(s.select(q(1,1, region='unused')), [])


if __name__ == '__main__':
    unittest.main()
