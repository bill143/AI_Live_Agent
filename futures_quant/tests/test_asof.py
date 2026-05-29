from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from futures_quant.data.asof import AsOfSeries
from futures_quant.exceptions import DataValidationError, LookAheadError

from futures_quant.tests._helpers import bar, consecutive

_BASE = datetime(2024, 3, 1, 0, 0, tzinfo=timezone.utc)


class TestAsOf(unittest.TestCase):
    def test_as_of_excludes_future_bars(self) -> None:
        series = AsOfSeries(consecutive(10))
        # Query at the close of bar #4 (base + 4 min): bars 0..4 are knowable.
        t = _BASE + timedelta(minutes=4)
        window = series.as_of(t)
        self.assertEqual(len(window), 5)
        self.assertEqual(window[-1].ts, t)
        # The most important property: no bar in the window closes after t.
        self.assertTrue(all(b.ts <= t for b in window))

    def test_as_of_strictly_before_first_is_empty(self) -> None:
        series = AsOfSeries(consecutive(5))
        before = _BASE - timedelta(minutes=1)
        self.assertEqual(series.as_of(before), ())

    def test_as_of_between_bars_does_not_leak_next(self) -> None:
        series = AsOfSeries(consecutive(5))
        # 30 seconds after bar #2's close, before bar #3 closes.
        t = _BASE + timedelta(minutes=2, seconds=30)
        window = series.as_of(t)
        self.assertEqual(len(window), 3)  # bars 0,1,2 only — not bar 3
        self.assertEqual(window[-1].ts, _BASE + timedelta(minutes=2))

    def test_naive_query_rejected(self) -> None:
        series = AsOfSeries(consecutive(3))
        with self.assertRaises(LookAheadError):
            series.as_of(datetime(2024, 3, 1, 0, 1))  # naive

    def test_unordered_construction_rejected(self) -> None:
        with self.assertRaises(DataValidationError):
            AsOfSeries([bar(3), bar(1)])

    def test_at_or_raise_exact_match(self) -> None:
        series = AsOfSeries(consecutive(5))
        b = series.at_or_raise(_BASE + timedelta(minutes=2))
        self.assertEqual(b.ts, _BASE + timedelta(minutes=2))

    def test_at_or_raise_non_close_raises(self) -> None:
        series = AsOfSeries(consecutive(5))
        with self.assertRaises(LookAheadError):
            series.at_or_raise(_BASE + timedelta(minutes=2, seconds=30))

    def test_latest_as_of(self) -> None:
        series = AsOfSeries(consecutive(5))
        latest = series.latest_as_of(_BASE + timedelta(minutes=3, seconds=10))
        assert latest is not None
        self.assertEqual(latest.ts, _BASE + timedelta(minutes=3))


if __name__ == "__main__":
    unittest.main()
