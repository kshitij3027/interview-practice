#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
import ast
from pathlib import Path
for path in [Path('fiber_ops.py'), *Path('netops').glob('*.py'), *Path('tests').glob('*.py')]:
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    print('syntax ok:', path)
PY
