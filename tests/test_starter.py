import json
import subprocess
import sys
import unittest
from rackfit import load_catalog, parse_event, ReservationEngine


class StarterTests(unittest.TestCase):
    def test_catalog(self):
        volumes, spans = load_catalog('fixtures')
        self.assertEqual(len(volumes), 6)
        self.assertEqual(len(spans), 11)
        self.assertEqual(volumes['v-90'][1], 10**12)

    def test_release_parser(self):
        event = parse_event('{"event_id":"e","op":"release","reservation_id":"r","extra":1}', {'GPU'})
        self.assertEqual(event, {'event_id':'e','op':'release','reservation_id':'r'})

    def test_invalid_number(self):
        for value in (True, 1.0, '1', 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_event(json.dumps(dict(event_id='e', op='allocate', reservation_id='r', pool='GPU', blocks=value, alignment=1)), {'GPU'})

    def test_invalid_pool(self):
        with self.assertRaises(ValueError):
            parse_event('{"event_id":"e","op":"allocate","reservation_id":"r","pool":"X","blocks":1,"alignment":1}', {'GPU'})

    def test_cli(self):
        run = subprocess.run([sys.executable, 'rackfit.py'], capture_output=True, text=True, check=True)
        results = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(len(results), 18)
        self.assertEqual(results[14], {'status':'invalid_event','line':15})
        self.assertEqual(results[16], {'status':'invalid_event','line':17})
        self.assertEqual(results[0]['event_id'], 'e1')


if __name__ == '__main__':
    unittest.main()
