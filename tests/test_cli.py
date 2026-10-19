import contextlib
import io
import unittest
from pathlib import Path

from market_book import main


class CliTests(unittest.TestCase):
    def test_validate_baseline(self):
        base = Path(__file__).resolve().parent.parent
        with io.StringIO() as out, contextlib.redirect_stdout(out):
            code = main(["validate", "--events", str(base / "fixtures/updates.csv"), "--queries", str(base / "fixtures/queries.jsonl")])
            text = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("17 unique updates", text)
        self.assertIn("3 invalid", text)

    def test_invalid_input_file(self):
        with io.StringIO() as err, contextlib.redirect_stderr(err):
            code = main(["validate", "--events", "does-not-exist.csv", "--queries", "anything.jsonl"])
            self.assertEqual(code, 2)
            self.assertIn("snapshot error", err.getvalue())


if __name__ == "__main__":
    unittest.main()
