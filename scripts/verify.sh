#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
node tests/smoke.mjs
