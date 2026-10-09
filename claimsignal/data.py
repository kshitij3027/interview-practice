"""Catalog and request parsing shared by CLI and resolver."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

CHANNELS = frozenset({"email", "phone", "chat"})
COLUMNS = ("rule_id", "issue_code", "phrase", "weight", "channels", "active")
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
PHRASE_PATTERN = re.compile(r"^[A-Za-z0-9 -]{1,120}$")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    issue_code: str
    phrase: str
    weight: int
    channels: frozenset[str]
    active: bool


@dataclass(frozen=True)
class Case:
    case_id: str
    channel: str
    text: str
    max_findings: int


def _channels(raw: str) -> frozenset[str]:
    if raw == "*":
        return CHANNELS
    parts = raw.split("|")
    if not parts or len(parts) != len(set(parts)) or not set(parts) <= CHANNELS:
        raise ValueError("invalid rule channels")
    return frozenset(parts)


def load_rules(path: str | Path) -> list[Rule]:
    rules: dict[str, tuple[dict[str, str], Rule]] = {}
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("catalog header mismatch")
        for line_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("invalid column count")
                rule_id = row["rule_id"]
                phrase = row["phrase"]
                if not ID_PATTERN.fullmatch(rule_id):
                    raise ValueError("invalid rule ID")
                if not CODE_PATTERN.fullmatch(row["issue_code"]):
                    raise ValueError("invalid issue code")
                if not PHRASE_PATTERN.fullmatch(phrase) or phrase.strip() != phrase or "  " in phrase or not any(ch.isalnum() for ch in phrase):
                    raise ValueError("invalid phrase")
                weight_text = row["weight"]
                if not weight_text.isascii() or not weight_text.isdecimal():
                    raise ValueError("invalid weight")
                weight = int(weight_text)
                if not 1 <= weight <= 100:
                    raise ValueError("invalid weight range")
                if row["active"] not in {"true", "false"}:
                    raise ValueError("invalid active flag")
                rule = Rule(rule_id, row["issue_code"], phrase, weight, _channels(row["channels"]), row["active"] == "true")
                if rule_id in rules:
                    if rules[rule_id][0] != row:
                        raise ValueError("conflicting rule replay")
                else:
                    rules[rule_id] = (row, rule)
            except ValueError as exc:
                raise ValueError(f"catalog line {line_number}: {exc}") from exc
    return [entry[1] for entry in rules.values()]


def parse_case_record(value: object) -> Case:
    if not isinstance(value, dict):
        raise ValueError("request must be an object")
    case_id = value.get("case_id")
    channel = value.get("channel")
    text = value.get("text")
    count = value.get("max_findings")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("invalid case ID")
    if channel not in CHANNELS:
        raise ValueError("invalid channel")
    if not isinstance(text, str) or any(ord(ch) > 127 for ch in text):
        raise ValueError("text must be ASCII")
    if type(count) is not int or not 1 <= count <= 8:
        raise ValueError("invalid finding limit")
    return Case(case_id, channel, text, count)


def iter_case_requests(path: str | Path) -> Iterator[tuple[Case | None, dict]]:
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            raw: object = None
            try:
                raw = json.loads(line)
                case = parse_case_record(raw)
                yield case, {}
            except (ValueError, TypeError):
                case_id = raw.get("case_id") if isinstance(raw, dict) else None
                if not isinstance(case_id, str) or not case_id.strip():
                    case_id = None
                yield None, {"case_id": case_id, "status": "invalid", "reason": "invalid_request"}
