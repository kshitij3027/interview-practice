import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
PLANNER = ROOT / "planner.py"
SERVICES = ROOT / "fixtures" / "services.csv"
DEPENDENCIES = ROOT / "fixtures" / "dependencies.csv"
INCIDENTS = ROOT / "fixtures" / "incidents.jsonl"

# Derived from the implementation and hand-checked against the README ordering rules.
GOLDEN_RESULTS = [
    {
        "incident_id": "inc-identity",
        "waves": [
            ["identity"],
            ["checkout"],
            ["fraud"],
            ["orders"],
            ["payments"],
            ["profile"],
            ["analytics"],
        ],
        "service_count": 7,
        "unknown_services": [],
        "ignored_dependency_rows": 2,
    },
    {
        "incident_id": "inc-shipping-west",
        "waves": [["inventory"], ["routing", "shipping"], ["returns"]],
        "service_count": 4,
        "unknown_services": [],
        "ignored_dependency_rows": 2,
    },
    {
        "incident_id": "inc-legacy-loop",
        "waves": [["legacy-sync", "partner-feed"]],
        "service_count": 2,
        "unknown_services": [],
        "ignored_dependency_rows": 2,
    },
    {
        "incident_id": "inc-mixed",
        "waves": [["catalog"], ["search"], ["recommendations"]],
        "service_count": 3,
        "unknown_services": ["does-not-exist"],
        "ignored_dependency_rows": 2,
    },
]


class CliTests(unittest.TestCase):
    def run_cli(
        self, incidents: Path = INCIDENTS, services: Path = SERVICES
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(PLANNER),
                "--services",
                str(services),
                "--dependencies",
                str(DEPENDENCIES),
                "--incidents",
                str(incidents),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def parsed_lines(stdout: str) -> list[object]:
        return [json.loads(line) for line in stdout.splitlines()]

    def test_golden_output_all_incidents(self):
        completed = self.run_cli()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(self.parsed_lines(completed.stdout), GOLDEN_RESULTS)

    def test_stdout_is_pure_jsonl_and_stderr_empty(self):
        completed = self.run_cli()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(len(completed.stdout.splitlines()), 4)
        self.parsed_lines(completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_deterministic_across_runs(self):
        first = self.run_cli()
        second = self.run_cli()
        self.assertEqual(first.returncode, second.returncode)
        self.assertEqual(first.stdout, second.stdout)

    def test_missing_input_file_exits_two(self):
        completed = self.run_cli(services=ROOT / "fixtures" / "missing.csv")
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertTrue(completed.stderr.strip())
        self.assertNotIn("Traceback", completed.stderr)

    def test_malformed_incident_line_exits_two_after_prior_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incidents.jsonl"
            good_lines = INCIDENTS.read_text(encoding="utf-8").splitlines()[:2]
            path.write_text("\n".join([*good_lines, "{bad json}"]) + "\n", encoding="utf-8")
            completed = self.run_cli(incidents=path)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(self.parsed_lines(completed.stdout), GOLDEN_RESULTS[:2])
        self.assertIn("incident line 3", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_non_object_incident_line_exits_two(self):
        completed = self._run_incident_text("[]\n")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("incident must be a JSON object", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_invalid_failed_services_type_exits_two(self):
        completed = self._run_incident_text(
            json.dumps({"incident_id": "bad", "failed_services": "identity"}) + "\n"
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("failed_services", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_empty_incidents_file(self):
        completed = self._run_incident_text("")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")

    def test_blank_lines_skipped(self):
        completed = self._run_incident_text("\n  \n\t\n")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")

    def test_help_exits_zero(self):
        completed = subprocess.run(
            [sys.executable, str(PLANNER), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")

    def _run_incident_text(self, content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incidents.jsonl"
            path.write_text(content, encoding="utf-8")
            return self.run_cli(incidents=path)


if __name__ == "__main__":
    unittest.main()
