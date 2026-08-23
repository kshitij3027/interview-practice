import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from planner import RecoveryPlanner
from scripts.bench_scale import nearest_rank


ROOT = Path(__file__).parent
GENERATOR = ROOT / "scripts" / "gen_scale_fixture.py"
BENCHMARK = ROOT / "scripts" / "bench_scale.py"


class ScaleGeneratorTests(unittest.TestCase):
    def test_generator_is_deterministic_and_contains_adversarial_rows(self):
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = Path(first_tmp)
            second = Path(second_tmp)
            arguments = [
                "--services", "1000", "--dependency-rows", "7000",
                "--cluster-size", "100", "--seed", "17",
            ]
            for output in (first, second):
                completed = subprocess.run(
                    [sys.executable, str(GENERATOR), "--out", str(output), *arguments],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

            self.assertEqual(
                (first / "services.csv").read_bytes(),
                (second / "services.csv").read_bytes(),
            )
            self.assertEqual(
                (first / "dependencies.csv").read_bytes(),
                (second / "dependencies.csv").read_bytes(),
            )
            with (first / "dependencies.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 7000)
            self.assertTrue(any(row["kind"] == "soft" for row in rows))
            self.assertTrue(any(row["depends_on"].startswith("unknown-") for row in rows))
            self.assertTrue(any(row["service_id"] == row["depends_on"] for row in rows))
            hard_pairs = [
                (row["service_id"], row["depends_on"])
                for row in rows if row["kind"] == "hard"
            ]
            self.assertLess(len(set(hard_pairs)), len(hard_pairs))


class ScaleBenchmarkTests(unittest.TestCase):
    def test_nearest_rank_convention(self):
        self.assertEqual(nearest_rank([5, 1, 4, 2, 3], 0.50), 3)
        self.assertEqual(nearest_rank([5, 1, 4, 2, 3], 0.95), 5)

    def test_diagnostics_match_uninstrumented_result(self):
        planner = RecoveryPlanner.from_paths(
            ROOT / "fixtures" / "services.csv",
            ROOT / "fixtures" / "dependencies.csv",
        )
        incident = {"incident_id": "i", "failed_services": ["identity"]}
        diagnosed = planner.diagnose(incident)
        self.assertEqual(diagnosed["result"], planner.plan(incident))
        metrics = diagnosed["diagnostics"]
        self.assertEqual(metrics["reached_nodes"], 7)
        self.assertGreaterEqual(metrics["reverse_edges_scanned"], 6)
        self.assertEqual(metrics["wave_count"], 7)
        self.assertEqual(metrics["scc_count"], 7)

    def test_quick_end_to_end_runs_all_isolated_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            completed = subprocess.run(
                [
                    sys.executable, str(BENCHMARK),
                    "--services", "800",
                    "--dependency-rows", "4000",
                    "--cluster-size", "100",
                    "--samples-per-stratum", "3",
                    "--warmup", "2",
                    "--throughput-queries", "20",
                    "--sweep-repetitions", "1",
                    "--allow-insufficient-samples",
                    "--report", str(report_path),
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(
            report["methodology"]["process_isolation"],
            ["A-timing", "B-memory", "C-diagnostics"],
        )
        self.assertEqual(report["latency"]["verdict"], "insufficient_samples")
        self.assertEqual(report["memory"]["verdict"], "pass")
        self.assertEqual(len(report["diagnostics"]["records"]), 24)
        self.assertEqual(report["latency"]["throughput"]["queries"], 20)
        self.assertEqual(len(report["latency"]["hub_region_sweep"]), 20)
        self.assertEqual(
            sum(
                sample["point"].startswith("after_sweep:")
                for sample in report["memory"]["samples"]
            ),
            20,
        )
        self.assertTrue(
            all(sample["raw_unit"] in {"bytes", "KiB"} for sample in report["memory"]["samples"])
        )


if __name__ == "__main__":
    unittest.main()
