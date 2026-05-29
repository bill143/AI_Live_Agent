from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from futures_quant.data.ninjatrader import NinjaTraderFormat, parse_export
from futures_quant.exceptions import DataValidationError, FormatNotConfirmedError


def _chicago_available() -> bool:
    try:
        from zoneinfo import ZoneInfo

        ZoneInfo("America/Chicago")
        return True
    except Exception:  # noqa: BLE001
        return False


class TestNinjaTraderAdapter(unittest.TestCase):
    def test_unconfirmed_format_refuses_to_parse(self) -> None:
        # The default format is the UNCONFIRMED sentinel: it must NOT guess.
        fmt = NinjaTraderFormat()
        self.assertFalse(fmt.confirmed)
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
            fh.write("20240301 093000;18000.00;18001.00;17999.00;18000.25;100\n")
            path = fh.name
        with self.assertRaises(FormatNotConfirmedError):
            parse_export(path, fmt, symbol="NQ", contract="NQH24")
        Path(path).unlink()

    def test_missing_file_raises(self) -> None:
        fmt = NinjaTraderFormat(
            source_timezone="UTC",
            timestamp_edge="close",
            datetime_format="%Y%m%d %H%M%S",
        )
        with self.assertRaises(DataValidationError):
            parse_export("/nonexistent/nq.csv", fmt, symbol="NQ", contract="NQH24")

    def test_confirmed_utc_close_parses(self) -> None:
        fmt = NinjaTraderFormat(
            source_timezone="UTC",
            timestamp_edge="close",
            datetime_format="%Y%m%d %H%M%S",
            delimiter=";",
            has_header=False,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
            fh.write("20240301 093000;18000.00;18001.00;17999.00;18000.25;100\n")
            fh.write("20240301 093100;18000.25;18002.00;18000.00;18001.50;120\n")
            path = fh.name
        bars = parse_export(path, fmt, symbol="NQ", contract="NQH24")
        Path(path).unlink()
        self.assertEqual(len(bars), 2)
        # close edge + UTC: timestamp passes through unchanged, just made aware.
        self.assertEqual(bars[0].ts, datetime(2024, 3, 1, 9, 30, tzinfo=timezone.utc))

    @unittest.skipUnless(_chicago_available(), "America/Chicago tz data unavailable")
    def test_open_edge_shifts_to_close_and_converts_tz(self) -> None:
        # Chicago on 2024-03-01 is CST (UTC-6, pre-DST). An 'open' stamp at
        # 09:30 local becomes a 'close' at 09:31 local = 15:31 UTC.
        fmt = NinjaTraderFormat(
            source_timezone="America/Chicago",
            timestamp_edge="open",
            datetime_format="%Y%m%d %H%M%S",
            delimiter=";",
            has_header=False,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
            fh.write("20240301 093000;18000.00;18001.00;17999.00;18000.25;100\n")
            path = fh.name
        bars = parse_export(path, fmt, symbol="NQ", contract="NQH24")
        Path(path).unlink()
        self.assertEqual(bars[0].ts, datetime(2024, 3, 1, 15, 31, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
