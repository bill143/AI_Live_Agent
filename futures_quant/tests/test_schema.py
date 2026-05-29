from __future__ import annotations

import unittest
from datetime import datetime
from decimal import Decimal

from futures_quant.data.schema import (
    CANONICAL_COLUMNS,
    Bar,
    parse_row,
    read_canonical_csv,
    to_csv_rows,
)
from futures_quant.exceptions import DataValidationError


def _row(**overrides: str) -> dict[str, str]:
    base = {
        "timestamp": "2024-03-01T00:01:00Z",
        "open": "18000.00",
        "high": "18001.00",
        "low": "17999.00",
        "close": "18000.25",
        "volume": "100",
        "symbol": "NQ",
        "contract": "NQH24",
    }
    base.update(overrides)
    return base


class TestSchema(unittest.TestCase):
    def test_parse_valid_row(self) -> None:
        b = parse_row(_row(), line=2)
        self.assertEqual(b.open, Decimal("18000.00"))
        self.assertEqual(b.volume, 100)
        self.assertIsNotNone(b.ts.tzinfo)

    def test_naive_timestamp_rejected(self) -> None:
        with self.assertRaises(DataValidationError):
            Bar(
                ts=datetime(2024, 3, 1, 0, 1),  # naive
                open=Decimal("1"), high=Decimal("1"), low=Decimal("1"),
                close=Decimal("1"), volume=1, symbol="NQ", contract="NQH24",
            )

    def test_bad_decimal_rejected(self) -> None:
        with self.assertRaises(DataValidationError):
            parse_row(_row(close="not-a-number"), line=2)

    def test_bad_volume_rejected(self) -> None:
        with self.assertRaises(DataValidationError):
            parse_row(_row(volume="12.5"), line=2)

    def test_missing_column_rejected(self) -> None:
        row = _row()
        del row["high"]
        with self.assertRaises(DataValidationError):
            parse_row(row, line=2)

    def test_roundtrip_csv_rows(self) -> None:
        b = parse_row(_row(), line=2)
        rows = list(to_csv_rows([b]))
        self.assertEqual(tuple(rows[0]), CANONICAL_COLUMNS)
        self.assertEqual(rows[1][6], "NQ")

    def test_read_missing_file_raises(self) -> None:
        with self.assertRaises(DataValidationError):
            read_canonical_csv("/nonexistent/path/to/data.csv")


if __name__ == "__main__":
    unittest.main()
