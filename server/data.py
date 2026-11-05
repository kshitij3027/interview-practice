"""Read the fixture workspace without external packages."""
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load_workspace():
    with (FIXTURES / "workspace.json").open(encoding="utf-8") as file:
        return json.load(file)


def load_activity():
    records = []
    with (FIXTURES / "activity.jsonl").open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    records.append({"_invalid": line.strip()})
    return records
