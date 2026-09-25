#!/usr/bin/env bash
set -euo pipefail
go run ./cmd/windowfinder validate --pools fixtures/pools.csv --events fixtures/capacity_events.csv --reservations fixtures/reservations.csv --queries fixtures/queries.jsonl
