from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from futures_quant.data.roll import (
    CalendarRoll,
    ContractSeries,
    VolumeRoll,
    build_continuous,
)
from futures_quant.data.schema import Bar
from futures_quant.exceptions import DataValidationError


def _daily(day: int, contract: str, *, close: str = "18000.00", volume: int = 100) -> Bar:
    """One synthetic daily bar in March 2024 for a given contract."""
    return Bar(
        ts=datetime(2024, 3, day, 16, 0, tzinfo=timezone.utc),
        open=Decimal("18000.00"),
        high=Decimal("18001.00"),
        low=Decimal("17999.00"),
        close=Decimal(close),
        volume=volume,
        symbol="NQ",
        contract=contract,
    )


class TestCalendarRoll(unittest.TestCase):
    def setUp(self) -> None:
        self.front = ContractSeries(
            contract="NQH24",
            expiry=date(2024, 3, 15),
            bars=tuple(_daily(d, "NQH24") for d in (8, 9, 10, 11, 12)),
        )
        self.back = ContractSeries(
            contract="NQM24",
            expiry=date(2024, 6, 21),
            bars=tuple(_daily(d, "NQM24") for d in (9, 10, 11, 12, 13)),
        )

    def test_rolls_five_days_before_expiry(self) -> None:
        result = build_continuous([self.front, self.back], CalendarRoll(5))
        # Roll fires on 2024-03-10 (5 days before 03-15 expiry).
        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].from_contract, "NQH24")
        self.assertEqual(result.events[0].to_contract, "NQM24")
        self.assertEqual(result.events[0].ts.date(), date(2024, 3, 10))

    def test_no_time_overlap_and_no_double_count(self) -> None:
        result = build_continuous([self.front, self.back], CalendarRoll(5))
        times = [b.ts for b in result.bars]
        self.assertEqual(times, sorted(times))
        self.assertEqual(len(times), len(set(times)))  # no duplicate instants

    def test_front_before_roll_then_back_after(self) -> None:
        result = build_continuous([self.front, self.back], CalendarRoll(5))
        # Before 03-10 the active contract is the front; on/after it's the back.
        for b in result.bars:
            if b.ts.date() < date(2024, 3, 10):
                self.assertEqual(b.contract, "NQH24")
            else:
                self.assertEqual(b.contract, "NQM24")

    def test_prices_not_back_adjusted(self) -> None:
        # Give the contracts different price levels; continuous series must keep
        # each bar's real traded price (no back-adjustment smoothing).
        front = ContractSeries(
            "NQH24", date(2024, 3, 15),
            tuple(_daily(d, "NQH24", close="18000.00") for d in (8, 9, 10)),
        )
        back = ContractSeries(
            "NQM24", date(2024, 6, 21),
            tuple(_daily(d, "NQM24", close="18150.00") for d in (9, 10, 11)),
        )
        result = build_continuous([front, back], CalendarRoll(5))
        closes = {b.contract: b.close for b in result.bars}
        self.assertEqual(closes["NQH24"], Decimal("18000.00"))
        self.assertEqual(closes["NQM24"], Decimal("18150.00"))


class TestVolumeRoll(unittest.TestCase):
    def test_rolls_on_volume_crossover(self) -> None:
        front = ContractSeries(
            "NQH24", date(2024, 3, 15),
            tuple(_daily(d, "NQH24", volume=v) for d, v in
                  ((8, 1000), (9, 800), (10, 400), (11, 200))),
        )
        back = ContractSeries(
            "NQM24", date(2024, 6, 21),
            tuple(_daily(d, "NQM24", volume=v) for d, v in
                  ((8, 100), (9, 500), (10, 900), (11, 1500))),
        )
        result = build_continuous([front, back], VolumeRoll())
        # Back overtakes front on 03-09 (500 > 800? no; 03-10: 900 > 400 yes).
        self.assertEqual(result.events[0].ts.date(), date(2024, 3, 10))


class TestRollGuards(unittest.TestCase):
    def test_empty_raises(self) -> None:
        with self.assertRaises(DataValidationError):
            build_continuous([], CalendarRoll(5))

    def test_unordered_expiries_raise(self) -> None:
        a = ContractSeries("NQM24", date(2024, 6, 21), (_daily(8, "NQM24"),))
        b = ContractSeries("NQH24", date(2024, 3, 15), (_daily(9, "NQH24"),))
        with self.assertRaises(DataValidationError):
            build_continuous([a, b], CalendarRoll(5))


if __name__ == "__main__":
    unittest.main()
