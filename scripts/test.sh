#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ruby -Itest test/store_test.rb
ruby -Itest test/subscription_service_test.rb
ruby -Itest test/routes_test.rb
