#!/usr/bin/env bash
set -euo pipefail
ruby -rjson -e 'd=JSON.parse(File.read("fixtures/sites.json")); abort unless d["readings"].map{|r|r["id"]}.uniq.size==d["readings"].size; puts "#{d["sites"].size} sites, #{d["meters"].size} meters, #{d["readings"].size} readings"'
