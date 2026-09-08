#!/usr/bin/env bash
set -euo pipefail
ruby -c server.rb >/dev/null
for file in lib/*.rb test/*.rb; do ruby -c "$file" >/dev/null; done
node --check web/api.js
node --check web/store.js
node --check web/app.js
ruby -rjson -e 'JSON.parse(File.read("fixtures/employees.json")); JSON.parse(File.read("fixtures/shifts.json")); puts "Ruby/JS syntax and fixtures verified"'
