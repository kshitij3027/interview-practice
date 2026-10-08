#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
node --input-type=module -e 'import {loadBins} from "./lib/catalog.js"; import {readFileSync,readdirSync} from "node:fs"; const rows=readdirSync("fixtures").filter(p=>p.startsWith("count_scans_")).flatMap(p=>readFileSync("fixtures/"+p,"utf8").trim().split("\n").map(JSON.parse)); console.log("validated " + loadBins().length + " bins / " + rows.length + " scan events");'
./scripts/test.sh
./scripts/build.sh
