from __future__ import annotations

import unittest
from datetime import timedelta
from decimal import Decimal

from futures_quant.data.validation import validate_bars
from futures_quant.exceptions import DataValidationError

from futures_quant.tests._helpers import bar, consecutive


class TestValidation(unittest.TestCase):
    def test_clean_series_passes(self) -> None:
        report = validate_bars(consecutive(10), contract="NQH24")
        self.assertEqual(report.n_bars, 10)
        self.assertFalse(report.has_gaps)

    def test_empty_raises(self) -> None:
        with self.assertRaises(DataValidationError):
            validate_bars([], contract="NQH24")

    def test_duplicate_timestamp_raises(self) -> None:
        bars = [bar(0), bar(0)]  # same minute twice
        with self.assertRaises(DataValidationError):
            validate_bars(bars, contract="NQH24")

    def test_backwards_timestamp_raises(self) -> None:
        bars = [bar(5), bar(3)]
        with self.assertRaises(DataValidationError):
            validate_bars(bars, contract="NQH24")

    def test_off_tick_grid_raises(self) -> None:
        bars = [bar(0, c="18000.30")]  # 0.30 is not on the 0.25 grid
        with self.assertRaises(DataValidationError):
            validate_bars(bars, contract="NQH24")

    def test_ohlc_inconsistent_raises(self) -> None:
        # high below the open is impossible
        bars = [bar(0, o="18000.00", h="17999.00", l="17998.00", c="17999.00")]
        with self.assertRaises(DataValidationError):
            validate_bars(bars, contract="NQH24")

    def test_negative_volume_raises(self) -> None:
        bars = [bar(0, volume=-1)]
        with self.assertRaises(DataValidationError):
            validate_bars(bars, contract="NQH24")

    def test_wrong_contract_raises(self) -> None:
        bars = [bar(0, contract="NQM24")]
        with self.assertRaises(DataValidationError):
            validate_bars(bars, contract="NQH24")

    def test_gap_reported_not_filled(self) -> None:
        # minute 0, then jump to minute 5 → a 4-interval gap, reported not filled
        bars = [bar(0), bar(5)]
        report = validate_bars(bars, contract="NQH24", bar_interval=timedelta(minutes=1))
        self.assertTrue(report.has_gaps)
        self.assertEqual(len(report.gaps), 1)
        self.assertEqual(report.gaps[0].missing_intervals, 4)
        # Crucially, the bar count is unchanged — nothing was invented.
        self.assertEqual(report.n_bars, 2)


if __name__ == "__main__":
    unittest.main()
