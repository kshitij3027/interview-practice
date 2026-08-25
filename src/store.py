import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CaseStore:
    def __init__(self, path=None):
        source = Path(path) if path else ROOT / "fixtures" / "cases.json"
        self._cases = {item["id"]: item for item in json.loads(source.read_text())}

    def list_cases(self):
        return copy.deepcopy(sorted(self._cases.values(), key=lambda c: c["id"]))

    def get_case(self, case_id):
        case = self._cases.get(case_id)
        return copy.deepcopy(case) if case else None

    def add_note(self, case_id, text, expected_revision):
        case = self._cases.get(case_id)
        if not case:
            raise KeyError("case_not_found")
        if case["revision"] != expected_revision:
            raise ValueError("stale_revision")
        clean = text.strip() if isinstance(text, str) else ""
        if not clean:
            raise ValueError("invalid_note")
        note = {"id": f"n-{len(case['notes']) + 100}", "text": clean, "author": "operator"}
        case["notes"].append(note)
        case["revision"] += 1
        return copy.deepcopy(case)
