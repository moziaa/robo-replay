import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from robo_replay import report, summarize

EXAMPLE = json.loads(Path(__file__).with_name('example.json').read_text())

class NotebookTests(unittest.TestCase):
    def test_comparison_separates_failure_timing(self):
        result = summarize(EXAMPLE)
        straight = next(g for g in result if g['variant'] == 'straight scoop')
        self.assertEqual((straight['successes'], straight['attempts']), (1, 2))
        self.assertEqual(straight['median_seconds_all'], 16.5)
        self.assertEqual(straight['median_seconds_successful'], 18)
        self.assertEqual(straight['success_percent'], 50)
        self.assertIn('Rails will repeat', report(result))

    def test_all_failures_have_no_success_time(self):
        data = copy.deepcopy(EXAMPLE)
        for r in data['runs']: r['success'] = False
        self.assertTrue(all(g['median_seconds_successful'] is None for g in summarize(data)))
        self.assertIn('n/a', report(summarize(data)))

    def test_distinct_missions_stay_separate(self):
        data = copy.deepcopy(EXAMPLE)
        data['runs'][1]['mission'] = 'Another mission'
        self.assertEqual(len(summarize(data)), 3)
        self.assertEqual(EXAMPLE['runs'][1]['mission'], 'Deliver a foam cube')

    def test_invalid_notebooks(self):
        cases = [None, [], {}, {'schema_version': 1, 'runs': []}]
        for field, value in [('seconds', 0), ('seconds', -1), ('seconds', True),
                             ('seconds', float('nan')), ('seconds', float('inf')),
                             ('success', 1), ('prediction', ''), ('mission', None)]:
            data = copy.deepcopy(EXAMPLE)
            data['runs'][0][field] = value
            cases.append(data)
        duplicate = copy.deepcopy(EXAMPLE)
        duplicate['runs'][1]['id'] = duplicate['runs'][0]['id']
        cases.append(duplicate)
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError): summarize(data)

    def test_notes_cannot_add_html_or_table_rows(self):
        data = copy.deepcopy(EXAMPLE)
        data['runs'][0]['mission'] = '<script>x</script>|\nrow'
        text = report(summarize(data))
        self.assertNotIn('<script>', text)
        self.assertIn('\\| row', text)

    def test_schema_version_requires_integer(self):
        for version in (True, False, 1.0, '1', None, 2):
            data = copy.deepcopy(EXAMPLE)
            data['schema_version'] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                summarize(data)

    def test_duration_limits_prevent_nonfinite_medians(self):
        for seconds in (86400.1, 1e308, 10 ** 400):
            data = copy.deepcopy(EXAMPLE)
            data['runs'][0]['seconds'] = seconds
            with self.subTest(seconds=seconds), self.assertRaisesRegex(ValueError, '86400'):
                summarize(data)
        data = copy.deepcopy(EXAMPLE)
        for run in data['runs']:
            run['seconds'] = 86400
        self.assertTrue(all(g['median_seconds_all'] == 86400 for g in summarize(data)))
        json.dumps(summarize(data), allow_nan=False)

    def test_cli_rejects_huge_duration_without_traceback(self):
        script = str(Path(__file__).with_name('robo_replay.py'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'practice.json'
            data = copy.deepcopy(EXAMPLE)
            data['runs'][0]['seconds'] = 10 ** 400
            path.write_text(json.dumps(data))
            run = subprocess.run([sys.executable, script, str(path), '--json'],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 2)
            self.assertIn('86400', run.stderr)
            self.assertNotIn('Traceback', run.stderr)
            self.assertEqual(run.stdout, '')

    def test_cli_json_and_bad_input(self):
        script = str(Path(__file__).with_name('robo_replay.py'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'practice.json'
            original = json.dumps(EXAMPLE)
            path.write_text(original)
            run = subprocess.run([sys.executable, script, str(path), '--json'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(len(json.loads(run.stdout)), 2)
            self.assertEqual(path.read_text(), original)
            path.write_text('{bad')
            run = subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, '')

if __name__ == '__main__': unittest.main()
