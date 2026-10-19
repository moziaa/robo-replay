"""Compare robot practice experiments offline. Python 3.9+, standard library only."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import median


def validate(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Notebook must be an object with schema_version 1')
    runs = data.get('runs')
    if not isinstance(runs, list) or not runs:
        raise ValueError('runs must be a nonempty list')
    seen = set()
    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            raise ValueError('Run %s must be an object' % index)
        for field in ('id', 'mission', 'variant', 'prediction', 'observation'):
            if not isinstance(run.get(field), str) or not run[field].strip():
                raise ValueError('Run %s needs nonempty text for %s' % (index, field))
        if run['id'] in seen:
            raise ValueError('Duplicate run id: ' + run['id'])
        seen.add(run['id'])
        if type(run.get('success')) is not bool:
            raise ValueError('Run %s success must be true or false' % index)
        seconds = run.get('seconds')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('Run %s seconds must be a finite positive number' % index)
    return runs


def summarize(data):
    groups = defaultdict(list)
    for run in validate(data):
        groups[(run['mission'], run['variant'])].append(run)
    summary = []
    for (mission, variant), runs in sorted(groups.items()):
        successes = [run for run in runs if run['success']]
        summary.append({
            'mission': mission, 'variant': variant, 'attempts': len(runs),
            'successes': len(successes), 'success_percent': 100 * len(successes) / len(runs),
            'median_seconds_all': median(run['seconds'] for run in runs),
            'median_seconds_successful': median(run['seconds'] for run in successes) if successes else None,
            'reflections': [{'id': r['id'], 'prediction': r['prediction'],
                             'observation': r['observation']} for r in runs],
        })
    return summary


def safe_text(value):
    # Keep notes as literal text, not terminal controls or Markdown/HTML markup.
    value = ''.join(c if c.isprintable() else ' ' for c in str(value))
    for char in ('\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|', '>'):
        value = value.replace(char, '\\' + char)
    return value.replace('&', '&amp;').replace('<', '&lt;')


def report(summary):
    lines = ['# RoboReplay practice review', '',
             'Compare one change at a time under similar conditions. Counts are observations, not proof of improvement.', '',
             '| Mission | Variant | Successes / attempts | Success % | Median seconds (all) | Median seconds (successful) |',
             '| --- | --- | --- | --- | --- | --- |']
    for group in summary:
        success_time = group['median_seconds_successful']
        lines.append('| %s | %s | %s / %s | %.1f | %.2f | %s |' % (
            safe_text(group['mission']), safe_text(group['variant']), group['successes'], group['attempts'],
            group['success_percent'], group['median_seconds_all'],
            'n/a' if success_time is None else '%.2f' % success_time))
    lines += ['', '## Predict, test, reflect', '']
    for group in summary:
        lines += ['### %s / %s' % (safe_text(group['mission']), safe_text(group['variant'])), '']
        for reflection in group['reflections']:
            lines += ['- **%s** — Prediction: %s; observation: %s' % (
                safe_text(reflection['id']), safe_text(reflection['prediction']), safe_text(reflection['observation']))]
        lines += ['']
    lines += ['## Next experiment', '',
              '- What single change will we test next?',
              '- What will stay the same (start position, battery, surface)?',
              '- How many repeated trials will we run for each variant?',
              '- What result would change our prediction?', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notebook', type=Path)
    parser.add_argument('--json', action='store_true', help='Output structured comparison')
    args = parser.parse_args(argv)
    try:
        summary = summarize(json.loads(args.notebook.read_text(encoding='utf-8')))
    except (OSError, ValueError, OverflowError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2, allow_nan=False) if args.json else report(summary))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
