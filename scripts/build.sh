#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile data_io.py gallery.py main.py tests_baseline.py
