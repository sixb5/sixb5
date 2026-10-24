"""Catch silent count loss, wrong date windows and incorrect streaks."""
import unittest
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import requests

from scripts.fetch_contributions import build_payload, compute_stats, main, parse_contributions


class ParseTests(unittest.TestCase):
    def test_modern_tooltips_are_joined_by_id_not_position(self):
        html = '''<table><td id="b" data-date="2026-01-02" data-level="4"></td>
        <td id="a" data-date="2026-01-01" data-level="0"></td></table>
        <tool-tip for="a">No contributions on January 1st.</tool-tip>
        <tool-tip for="b">1,234 contributions on January 2nd.</tool-tip>'''
        self.assertEqual(parse_contributions(html), [
            {"date": "2026-01-01", "count": 0, "level": 0},
            {"date": "2026-01-02", "count": 1234, "level": 4},
        ])

    def test_legacy_rect_counts(self):
        self.assertEqual(parse_contributions(
            '<svg><rect data-date="2024-02-29" data-count="7" data-level="2"/></svg>'
        ), [{"date": "2024-02-29", "count": 7, "level": 2}])

    def test_legacy_fill_keeps_positive_activity_visible(self):
        self.assertEqual(parse_contributions(
            '<svg><rect data-date="2026-01-01" data-count="12" fill="#26a641"/></svg>'
        ), [{"date": "2026-01-01", "count": 12, "level": 3}])

    def test_unknown_legacy_level_cannot_hide_positive_activity(self):
        with self.assertRaises(ValueError):
            parse_contributions('<rect data-date="2026-01-01" data-count="12"/>')

    def test_nonzero_cell_without_a_count_fails(self):
        with self.assertRaises(ValueError):
            parse_contributions('<td data-date="2026-01-01" data-level="2"></td>')

    def test_error_page_and_conflicting_duplicates_fail(self):
        for html in ['<h1>Rate limited</h1>',
                     '<rect data-date="2026-01-01" data-count="1" data-level="1"/>'
                     '<rect data-date="2026-01-01" data-count="3" data-level="2"/>']:
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_contributions(html)


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        self.days = [
            {"date": "2025-12-29", "count": 1, "level": 1},
            {"date": "2025-12-30", "count": 2, "level": 1},
            {"date": "2025-12-31", "count": 0, "level": 0},
            {"date": "2026-01-01", "count": 8, "level": 4},
            {"date": "2026-01-02", "count": 3, "level": 2},
            {"date": "2026-01-03", "count": 0, "level": 0},
        ]

    def test_totals_and_streak_ignore_input_order(self):
        stats = compute_stats(list(reversed(self.days)), date(2026, 1, 3))
        self.assertEqual(stats['total'], 14)
        self.assertEqual(stats['current_streak'], 2)
        self.assertEqual(stats['longest_streak'], 2)
        self.assertEqual(stats['active_days'], 4)
        self.assertEqual(stats['best_day'], {"date": "2026-01-01", "count": 8})
        self.assertEqual(stats['monthly_totals'], {"2025-12": 3, "2026-01": 11})

    def test_empty_yesterday_breaks_streak(self):
        self.assertEqual(compute_stats(self.days, date(2026, 1, 4))['current_streak'], 0)

    def test_all_zero_days_have_no_best_day(self):
        stats = compute_stats([{"date": "2026-01-01", "count": 0, "level": 0}], date(2026, 1, 1))
        self.assertEqual(stats['current_streak'], 0)
        self.assertIsNone(stats['best_day'])


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.end = date(2024, 3, 1)
        self.start = self.end - timedelta(days=364)
        self.days = [{"date": (self.start + timedelta(days=i)).isoformat(),
                      "count": 1, "level": 1} for i in range(365)]

    def test_leap_day_and_extra_outside_days(self):
        days = self.days + [{"date": "2024-03-02", "count": 999, "level": 4}]
        payload = build_payload('sixb5', list(reversed(days)), self.end)
        self.assertEqual(len(payload['days']), 365)
        self.assertEqual(payload['stats']['total'], 365)
        self.assertEqual(payload['stats']['longest_streak'], 365)
        self.assertEqual(payload['days'][-2]['date'], '2024-02-29')
        self.assertEqual(payload['range'], {"start": "2023-03-03", "end": "2024-03-01"})

    def test_missing_day_is_not_silently_filled_with_zero(self):
        with self.assertRaises(ValueError):
            build_payload('sixb5', self.days[1:], self.end)

    def test_duplicate_day_cannot_inflate_totals(self):
        payload = build_payload('sixb5', self.days + self.days, self.end)
        self.assertEqual(payload['stats']['total'], 365)


class FailureTests(unittest.TestCase):
    def test_network_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'contributions.json'
            output.write_text('last good data', encoding='utf-8')
            with patch('sys.argv', ['fetch_contributions.py', '--username', 'sixb5', '--output', str(output)]), \
                 patch('scripts.fetch_contributions.fetch_contributions', side_effect=requests.ConnectionError('offline')), \
                 patch('sys.stderr'), self.assertRaises(SystemExit) as exit_context:
                main()
            self.assertEqual(exit_context.exception.code, 1)
            self.assertEqual(output.read_text(encoding='utf-8'), 'last good data')


if __name__ == '__main__':
    unittest.main()
