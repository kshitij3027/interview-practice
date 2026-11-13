"""Starter tests verify existing interfaces, not the customer capability."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from tracecode.catalog import CatalogError, load_catalog
from tracecode.cli import main
from tracecode.contracts import parse_scan
from tracecode.engine import SerialRecovery

FIX = Path(__file__).resolve().parents[1] / "fixtures"


class StarterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(FIX / "models.csv", FIX / "ranges.csv")

    def test_model_and_range_loading(self):
        self.assertEqual(set(self.catalog.models), {"AX70", "BX20", "CX09"})
        self.assertEqual(len(self.catalog.bands["AX70"]), 3)

    def test_checksum_configuration_is_loaded(self):
        self.assertEqual(self.catalog.models["BX20"].weights, "29")
        self.assertEqual(self.catalog.models["AX70"].length, 12)

    def test_identical_range_retries_are_deduplicated(self):
        self.assertEqual(sum(map(len, self.catalog.bands.values())), 7)

    def test_scanned_choices_and_question_marks(self):
        obj = {"scan_id":"smoke","model_id":"BX20", "max_penalty":5,
               "reads":["?"]*9 + [{"7":0,"2":3}]}
        scan, error = parse_scan(json.dumps(obj), self.catalog)
        self.assertIsNone(error)
        self.assertEqual(scan.reads[0]["0"], 3)
        self.assertEqual(scan.reads[-1], {"7":0,"2":3})

    def test_bad_read_shape_is_isolated(self):
        obj = {"scan_id":"shape","model_id":"BX20","max_penalty":5,"reads":["?"]*9}
        scan, error = parse_scan(json.dumps(obj), self.catalog)
        self.assertIsNone(scan)
        self.assertEqual(error, {"scan_id":"shape","status":"invalid","reason":"invalid_scan"})

    def test_unknown_model_has_specific_error(self):
        obj={"scan_id":"missing","model_id":"XXX","max_penalty":4,"reads":[]}
        scan,error=parse_scan(json.dumps(obj),self.catalog)
        self.assertIsNone(scan)
        self.assertEqual(error["reason"],"unknown_model")

    def test_conflicting_model_is_catalog_error(self):
        with tempfile.TemporaryDirectory() as folder:
            models=Path(folder)/"models.csv"
            models.write_text("model_id,length,weights\nM,8,31\nM,9,31\n")
            with self.assertRaises(CatalogError):
                load_catalog(models, FIX / "ranges.csv")

    def test_cli_green_baseline(self):
        out=io.StringIO()
        with redirect_stdout(out):
            status=main(["recover","--models",str(FIX/"models.csv"),"--ranges",str(FIX/"ranges.csv"),"--scans",str(FIX/"scans.jsonl")])
        self.assertEqual(status,0)
        results=[json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(len(results),12)
        self.assertEqual(results[0]["status"],"not_implemented")
        self.assertTrue(any(x["status"]=="invalid" for x in results))

    def test_bad_catalog_writes_no_query_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            ranges=Path(folder)/"ranges.csv"
            ranges.write_text("range_id,model_id,first_payload,last_payload\nbad,AX70,1,2\n")
            out,err=io.StringIO(),io.StringIO()
            with redirect_stdout(out),redirect_stderr(err):
                status=main(["recover","--models",str(FIX/"models.csv"),"--ranges",str(ranges),"--scans",str(FIX/"scans.jsonl")])
            self.assertEqual(status,2)
            self.assertEqual(out.getvalue(),"")
            self.assertIn("invalid payload bounds",err.getvalue())


if __name__=="__main__":
    unittest.main()
