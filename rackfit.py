import argparse
import csv
import json
import re
import sys
from pathlib import Path

ID = re.compile(r'[A-Za-z0-9_-]{1,48}\Z')
MAX = 10**12
ALIGNMENTS = (1, 8, 64, 512, 4096)


def ident(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError('invalid identifier')
    return value


def number(value, minimum=0):
    if not isinstance(value, str) or not re.fullmatch(r'0|[1-9][0-9]*', value):
        raise ValueError('invalid CSV integer')
    n = int(value)
    if not minimum <= n <= MAX:
        raise ValueError('integer out of range')
    return n


def rows(path, fields):
    with open(path, newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream, strict=True)
        if sorted(reader.fieldnames or []) != sorted(fields):
            raise ValueError(f'{path}: invalid headers')
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f'{path}: invalid row')
            yield row


def load_catalog(directory):
    directory = Path(directory)
    volumes = {}
    for r in rows(directory / 'volumes.csv', ('volume_id', 'pool', 'capacity')):
        key = ident(r['volume_id'])
        value = (ident(r['pool']), number(r['capacity'], 1))
        if key in volumes and volumes[key] != value:
            raise ValueError('conflicting volume')
        volumes[key] = value
    reserved = []
    for r in rows(directory / 'reserved.csv', ('volume_id', 'start', 'end')):
        key = ident(r['volume_id'])
        start, end = number(r['start']), number(r['end'])
        if key not in volumes or not start < end <= volumes[key][1]:
            raise ValueError('invalid reserved span')
        reserved.append((key, start, end))
    return volumes, reserved


def parse_event(line, pools):
    raw = json.loads(line)
    if not isinstance(raw, dict):
        raise ValueError('expected object')
    event = {k: ident(raw.get(k)) for k in ('event_id', 'reservation_id')}
    op = raw.get('op')
    if op not in ('allocate', 'release'):
        raise ValueError('invalid operation')
    event['op'] = op
    if op == 'allocate':
        pool = ident(raw.get('pool'))
        blocks, alignment = raw.get('blocks'), raw.get('alignment')
        if pool not in pools or type(blocks) is not int or not 1 <= blocks <= MAX:
            raise ValueError('invalid allocation')
        if type(alignment) is not int or alignment not in ALIGNMENTS:
            raise ValueError('invalid alignment')
        event.update(pool=pool, blocks=blocks, alignment=alignment)
    return event


class ReservationEngine:
    def __init__(self, volumes, reserved):
        self.volumes = volumes
        self.reserved = reserved

    def apply(self, event):
        return {'event_id': event['event_id'], 'status': 'not_implemented'}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', default='fixtures')
    parser.add_argument('--events', default='fixtures/events.jsonl')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args(argv)
    try:
        volumes, reserved = load_catalog(args.catalog)
        pools = {pool for pool, _ in volumes.values()}
        if args.validate:
            print(json.dumps({'volumes': len(volumes), 'permanent_rows': len(reserved), 'pools': len(pools)}))
            return 0
        engine = ReservationEngine(volumes, reserved)
        with open(args.events, encoding='utf-8') as stream:
            for i, line in enumerate(stream, 1):
                try:
                    event = parse_event(line, pools)
                except ValueError:
                    result = {'status': 'invalid_event', 'line': i}
                else:
                    result = engine.apply(event)
                print(json.dumps(result, separators=(',', ':')))
        return 0
    except (OSError, ValueError, csv.Error) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
