"""POST-PRACTICE ONLY: exact behavioral oracle for small test snapshots."""

from __future__ import annotations

import random
import unittest
from pathlib import Path

from signalgate_pkg.catalog import Catalog, Signature, load_catalog
from signalgate_pkg.requests import ScanRequest, parse_request
from signalgate_pkg.scanner import SignalScanner

ROOT = Path(__file__).resolve().parents[1]


def oracle(catalog: Catalog, request: ScanRequest) -> dict:
    payload = b"".join(request.chunks)
    matches = []
    for sig in catalog.signatures:
        if not sig.enabled or sig.region not in ("*", request.region):
            continue
        if not sig.valid_from_ms <= request.seen_at_ms < sig.valid_until_ms:
            continue
        start = payload.find(sig.pattern)
        if start != -1:
            matches.append({"signature_id": sig.signature_id, "priority": sig.priority, "start": start})
    matches.sort(key=lambda x: (-x["priority"], x["start"], x["signature_id"]))
    return {"request_id": request.request_id, "status": "ok", "total_matching_signatures": len(matches),
            "matches": matches[:request.limit]}


class HiddenChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(ROOT / "fixtures/regions.csv", ROOT / "fixtures/signatures.csv")

    def test_fixture_requests_match_reference(self):
        scanner = SignalScanner(self.catalog)
        for row in (ROOT / "fixtures/requests.jsonl").read_text().splitlines():
            try:
                request = parse_request(row, self.catalog.regions)
            except ValueError:
                continue
            with self.subTest(request=request.request_id, time=request.seen_at_ms):
                self.assertEqual(scanner.scan(request), oracle(self.catalog, request))

    def test_chunk_boundary_with_empty_gap_and_overlaps(self):
        sigs = (Signature("long", "*", 40, 0, 10, b"abcd", True),
                Signature("inner", "east", 20, 0, 10, b"bc", True),
                Signature("early", "east", 20, 0, 10, b"c", True))
        catalog = Catalog(frozenset({"east"}), sigs)
        request = ScanRequest("cross", "east", 0, (b"c", b"a", b"", b"b", b"cd"), 2)
        self.assertEqual(SignalScanner(catalog).scan(request), oracle(catalog, request))
        self.assertEqual(oracle(catalog, request)["total_matching_signatures"], 3)

    def test_total_is_not_top_k_and_repeated_patterns_are_distinct(self):
        sigs = tuple(Signature(f"SIG_{i:04d}", "*", 100, 0, 100, b"a", True) for i in range(1000))
        catalog = Catalog(frozenset({"east"}), sigs)
        request = ScanRequest("dense", "east", 20, (b"aaaaa",), 1)
        self.assertEqual(SignalScanner(catalog).scan(request), oracle(catalog, request))
        self.assertEqual(oracle(catalog, request)["total_matching_signatures"], 1000)

    def test_shuffled_catalog_same_semantics(self):
        entries = list(self.catalog.signatures)
        request = ScanRequest("stable", "east", 250, (b"\x00ab", b"c", b"\xff\x00"), 12)
        expected = oracle(self.catalog, request)
        rng = random.Random(77)
        for _ in range(10):
            rng.shuffle(entries)
            actual = SignalScanner(Catalog(self.catalog.regions, tuple(entries))).scan(request)
            self.assertEqual(actual, expected)

    def test_deterministic_randomized_small_input_oracle(self):
        rng = random.Random(618)
        alphabet = b"ab\x00\xff"
        for iteration in range(60):
            sigs = []
            for i in range(rng.randrange(2, 25)):
                length = rng.randint(1, 5)
                pattern = bytes(rng.choice(alphabet) for _ in range(length))
                region = rng.choice(("*", "east", "west"))
                start = rng.randrange(0, 4)
                end = rng.randrange(start + 1, 10)
                sigs.append(Signature(f"sig_{i:03d}", region, rng.randrange(0, 5), start, end, pattern,
                                      rng.choice((True, True, False))))
            catalog = Catalog(frozenset({"east", "west"}), tuple(sigs))
            payload = bytes(rng.choice(alphabet) for _ in range(rng.randrange(0, 55)))
            chunks = []
            position = 0
            while position < len(payload):
                if rng.random() < 0.3:
                    chunks.append(b"")
                step = rng.randint(1, 5)
                chunks.append(payload[position:position + step])
                position += step
            if not chunks:
                chunks = [b""]
            request = ScanRequest(f"R_{iteration}", rng.choice(("east", "west")), rng.randrange(0, 11),
                                  tuple(chunks), rng.randint(1, 7))
            with self.subTest(iteration=iteration):
                self.assertEqual(SignalScanner(catalog).scan(request), oracle(catalog, request))


if __name__ == "__main__":
    unittest.main()
