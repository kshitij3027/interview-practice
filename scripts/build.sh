#!/usr/bin/env bash
set -euo pipefail
for f in server.php src/*.php tests/*.php; do php -l "$f" >/dev/null; done
for f in public/*.js; do node --check "$f"; done
php -r 'json_decode(file_get_contents("fixtures/accounts.json"), true, flags: JSON_THROW_ON_ERROR); json_decode(file_get_contents("fixtures/health_policy.json"), true, flags: JSON_THROW_ON_ERROR); foreach(file("fixtures/signals.jsonl", FILE_IGNORE_NEW_LINES|FILE_SKIP_EMPTY_LINES) as $l){json_decode($l,true,flags:JSON_THROW_ON_ERROR);} echo "Build verification passed\n";'
