set -eu
python3 rackfit.py --validate
python3 rackfit.py --events fixtures/events.jsonl
