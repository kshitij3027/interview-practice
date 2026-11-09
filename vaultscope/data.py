"""Input contracts and snapshot loader for VaultScope."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
QID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
NUM = re.compile(r"(?:0|[1-9][0-9]*)\Z")
MAX_TIME = 10**12


class InvalidCatalog(ValueError):
    pass


def identifier(value, *, query=False):
    pattern = QID if query else ID
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError("invalid identifier")
    return value


def number(value, low, high):
    if not isinstance(value, str) or not NUM.fullmatch(value):
        raise ValueError("invalid unsigned decimal")
    result = int(value)
    if not low <= result <= high:
        raise ValueError("integer out of range")
    return result


def csv_rows(filename, columns):
    with open(filename, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames is None or len(reader.fieldnames) != len(columns) or set(reader.fieldnames) != set(columns):
            raise InvalidCatalog(f"{filename}: incorrect CSV columns")
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise InvalidCatalog(f"{filename}:{line}: malformed CSV row")
            yield row, line


def declarations(filename, entity_col):
    result = {}
    for row, line in csv_rows(filename, [entity_col, "tenant_id"]):
        try:
            key = identifier(row[entity_col]); tenant = identifier(row["tenant_id"])
        except ValueError as error:
            raise InvalidCatalog(f"{filename}:{line}: {error}") from error
        if key in result and result[key] != tenant:
            raise InvalidCatalog(f"{filename}:{line}: conflicting {entity_col}")
        result[key] = tenant
    return result


def history(filename, cols, fields, validate):
    seen = {}
    for row, line in csv_rows(filename, cols):
        try:
            record_id = identifier(row[cols[0]])
            revision = number(row["revision"], 1, 10**9)
            op = row["op"]
            if op not in ("upsert", "delete"):
                raise ValueError("invalid operation")
            if op == "delete":
                if any(row[field] != "" for field in fields):
                    raise ValueError("delete fields must be empty")
                parsed = None
            else:
                parsed = validate(row)
        except ValueError as error:
            raise InvalidCatalog(f"{filename}:{line}: {error}") from error
        pair = (record_id, revision)
        record = (op, parsed)
        if pair in seen and seen[pair] != record:
            raise InvalidCatalog(f"{filename}:{line}: conflicting revision")
        seen[pair] = record
    winners = {}
    for (record_id, revision), (op, parsed) in seen.items():
        if record_id not in winners or revision > winners[record_id][0]:
            winners[record_id] = (revision, op, parsed)
    return seen, {key: item[2] for key, item in winners.items() if item[1] == "upsert"}


def parse_membership(row):
    subject_type = row["member_type"]
    if subject_type not in ("user", "group"):
        raise ValueError("invalid member type")
    start = number(row["active_from_ms"], 0, MAX_TIME)
    until = number(row["active_until_ms"], 0, MAX_TIME)
    if start >= until:
        raise ValueError("invalid membership interval")
    return (subject_type, identifier(row["member_id"]), identifier(row["group_id"]), start, until)


def parse_policy(row):
    subject_type = row["subject_type"]
    if subject_type not in ("user", "group"):
        raise ValueError("invalid subject type")
    if row["action"] not in ("view", "edit", "export"):
        raise ValueError("invalid action")
    if row["effect"] not in ("allow", "deny"):
        raise ValueError("invalid effect")
    start = number(row["active_from_ms"], 0, MAX_TIME)
    until = number(row["active_until_ms"], 0, MAX_TIME)
    if start >= until:
        raise ValueError("invalid policy interval")
    return (identifier(row["resource_id"]), subject_type, identifier(row["subject_id"]), row["action"], row["effect"], start, until)


def load_snapshot(root):
    root = Path(root)
    users = declarations(root / "users.csv", "user_id")
    groups = declarations(root / "groups.csv", "group_id")
    resources = declarations(root / "resources.csv", "resource_id")
    membership_fields = ["member_type", "member_id", "group_id", "active_from_ms", "active_until_ms"]
    policy_fields = ["resource_id", "subject_type", "subject_id", "action", "effect", "active_from_ms", "active_until_ms"]
    memberships_all, memberships = history(root / "memberships.csv", ["membership_id", "revision", "op"] + membership_fields, membership_fields, parse_membership)
    policies_all, policies = history(root / "policies.csv", ["policy_id", "revision", "op"] + policy_fields, policy_fields, parse_policy)

    # An invalid superseded row still makes an export untrustworthy.
    for op, data in memberships_all.values():
        if op == "delete":
            continue
        subject_type, member, group, _, _ = data
        source = users if subject_type == "user" else groups
        if member not in source or group not in groups or source[member] != groups[group]:
            raise InvalidCatalog("membership references missing or cross-tenant entity")
    for op, data in policies_all.values():
        if op == "delete":
            continue
        resource, kind, member, _, _, _, _ = data
        source = users if kind == "user" else groups
        if resource not in resources or member not in source or source[member] != resources[resource]:
            raise InvalidCatalog("policy references missing or cross-tenant entity")
    return {"users": users, "groups": groups, "resources": resources, "memberships": memberships, "policies": policies}


def parse_query(line):
    candidate_id = None
    try:
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("expected object")
        try:
            candidate_id = identifier(value.get("query_id"), query=True)
        except ValueError:
            pass
        query_id = identifier(value.get("query_id"), query=True)
        user = identifier(value.get("user_id"))
        resource = identifier(value.get("resource_id"))
        action = value.get("action")
        if action not in ("view", "edit", "export"):
            raise ValueError("invalid action")
        at = value.get("at_ms")
        if type(at) is not int or not (0 <= at <= MAX_TIME):
            raise ValueError("invalid time")
        return {"query_id": query_id, "user_id": user, "resource_id": resource, "action": action, "at_ms": at}, None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None, {"query_id": candidate_id, "status": "invalid", "reason": "invalid_query"}
