#!/usr/bin/env bash
set -euo pipefail
python3 -B -m unittest discover -s tests -p 'test_starter.py' -v
