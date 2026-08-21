import json
import tempfile
import unittest
from pathlib import Path

from planner import load_dependencies, load_incidents, load_services


class BaselineParsingTests(unittest.TestCase):
    def test_load_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "services.csv"
            path.write_text("service_id,tier,region\na,2,us-east\nb,1,us-west\n", encoding="utf-8")
            services = load_services(path)
            self.assertEqual(set(services), {"a", "b"})
            self.assertEqual(services["b"].tier, 1)

    def test_load_dependencies_preserves_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deps.csv"
            path.write_text(
                "service_id,depends_on,kind\na,b,hard\na,b,hard\nc,a,soft\n",
                encoding="utf-8",
            )
            deps = load_dependencies(path)
            self.assertEqual(len(deps), 3)
            self.assertEqual(deps[2].kind, "soft")

    def test_load_incidents_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incidents.jsonl"
            path.write_text(
                json.dumps({"incident_id": "i1", "failed_services": ["a"]}) + "\n",
                encoding="utf-8",
            )
            incidents = list(load_incidents(path))
            self.assertEqual(incidents[0]["incident_id"], "i1")


if __name__ == "__main__":
    unittest.main()
