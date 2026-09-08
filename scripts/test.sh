#!/usr/bin/env bash
set -euo pipefail
ruby -Itest test/store_test.rb
ruby -Itest test/schedule_service_test.rb
ruby -Itest test/router_test.rb
