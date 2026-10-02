import unittest

from locator.distance import great_circle_meters


class DistanceTests(unittest.TestCase):
    def test_same_coordinate_is_zero(self):
        self.assertAlmostEqual(great_circle_meters(10.0, 20.0, 10.0, 20.0), 0.0, places=9)

    def test_date_line_uses_short_way_around(self):
        distance = great_circle_meters(0.0, 179.9, 0.0, -179.9)
        self.assertGreater(distance, 20_000)
        self.assertLess(distance, 23_000)


if __name__ == "__main__":
    unittest.main()
