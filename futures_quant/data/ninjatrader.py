"""NinjaTrader CSV → canonical adapter.

This adapter is deliberately **inert until its format is confirmed against a
real sample export**. Building a vendor parser against guessed conventions is
exactly how a silent look-ahead or timezone bug gets baked in: if we assume the
export is UTC when it is exchange-local time, or assume bars are stamped at the
open when NinjaTrader stamps them at the close, every bar shifts and everything
downstream is quietly wrong.

So the parsing machinery is complete, but it refuses to run with the default
``UNCONFIRMED`` format. To enable it, drop a real export beside its three notes
and fill in a :class:`NinjaTraderFormat`:

    1. timezone of the export (e.g. "America/Chicago" or "UTC");
    2. timestamp_edge — does each bar's timestamp mark its "open" or "close"?
    3. has_header / delimiter / column order.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from ..exceptions import DataValidationError, FormatNotConfirmedError
from .schema import Bar

# Sentinel marking a format that has NOT been confirmed against a real file.
_UNCONFIRMED = "UNCONFIRMED"


@dataclass(frozen=True)
class NinjaTraderFormat:
    """Describes a specific NinjaTrader export so it can be parsed unambiguously.

    Defaults are the ``UNCONFIRMED`` sentinel: the adapter will refuse to parse
    until a real sample pins these down.
    """

    # Olson timezone name the export is written in, e.g. "America/Chicago".
    source_timezone: str = _UNCONFIRMED
    # Does each row's timestamp mark the bar's "open" or its "close"?
    timestamp_edge: str = _UNCONFIRMED
    # strptime format for the timestamp field, e.g. "%Y%m%d %H%M%S".
    datetime_format: str = _UNCONFIRMED
    delimiter: str = ";"
    has_header: bool = False
    # Order of fields in each row (canonical names). Timestamp first by default.
    column_order: tuple[str, ...] = (
        "timestamp", "open", "high", "low", "close", "volume",
    )
    bar_interval: timedelta = timedelta(minutes=1)

    @property
    def confirmed(self) -> bool:
        return _UNCONFIRMED not in (
            self.source_timezone,
            self.timestamp_edge,
            self.datetime_format,
        )

    def require_confirmed(self) -> None:
        if not self.confirmed:
            raise FormatNotConfirmedError(
                "NinjaTrader export format is not confirmed. Pin it against a "
                "real sample before parsing: set source_timezone, "
                "timestamp_edge ('open' or 'close'), and datetime_format. "
                "Parsing against guesses risks silent timezone / look-ahead bugs."
            )


def _resolve_tz(name: str) -> tzinfo:
    if name.upper() == "UTC":
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception as exc:  # noqa: BLE001 - surface any tz resolution failure loudly
        raise DataValidationError(
            f"Could not resolve timezone {name!r}: {exc}. Use an Olson name "
            f"like 'America/Chicago' or 'UTC'."
        ) from exc


def parse_export(
    path: str | Path,
    fmt: NinjaTraderFormat,
    *,
    symbol: str,
    contract: str,
) -> list[Bar]:
    """Parse one NinjaTrader export file into canonical :class:`Bar` objects.

    Converts the source timezone to UTC and, if the export stamps bars at the
    open, shifts the timestamp forward by one bar interval so the canonical
    timestamp marks the **close** (the moment the bar is knowable).

    Raises:
        FormatNotConfirmedError: if ``fmt`` has not been confirmed.
        DataValidationError: on structural/parse problems.
    """
    fmt.require_confirmed()

    p = Path(path)
    if not p.exists():
        raise DataValidationError(
            f"No NinjaTrader export at {p}; the adapter never fabricates bars."
        )

    src_tz = _resolve_tz(fmt.source_timezone)
    bars: list[Bar] = []

    with p.open(newline="") as fh:
        reader = csv.reader(fh, delimiter=fmt.delimiter)
        rows = list(reader)

    start = 1 if fmt.has_header else 0
    for line_no, row in enumerate(rows[start:], start=start + 1):
        if not row or all(not cell.strip() for cell in row):
            continue
        if len(row) < len(fmt.column_order):
            raise DataValidationError(
                f"{p}:{line_no}: expected {len(fmt.column_order)} columns "
                f"{fmt.column_order}, got {len(row)}: {row!r}."
            )
        record = dict(zip(fmt.column_order, (c.strip() for c in row)))

        try:
            naive = datetime.strptime(record["timestamp"], fmt.datetime_format)
        except ValueError as exc:
            raise DataValidationError(
                f"{p}:{line_no}: timestamp {record['timestamp']!r} does not "
                f"match format {fmt.datetime_format!r}."
            ) from exc

        local = naive.replace(tzinfo=src_tz)
        close_local = (
            local + fmt.bar_interval if fmt.timestamp_edge == "open" else local
        )
        close_utc = close_local.astimezone(timezone.utc)

        bars.append(
            Bar(
                ts=close_utc,
                open=Decimal(record["open"]),
                high=Decimal(record["high"]),
                low=Decimal(record["low"]),
                close=Decimal(record["close"]),
                volume=int(record["volume"]),
                symbol=symbol,
                contract=contract,
            )
        )

    if not bars:
        raise DataValidationError(f"{p}: no data rows parsed.")
    return bars


def write_canonical(bars: Sequence[Bar], out_path: str | Path) -> Path:
    """Write canonical bars to a CSV at ``out_path`` (helper for one-off conversion)."""
    from .schema import to_csv_rows

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as fh:
        writer = csv.writer(fh)
        for row in to_csv_rows(bars):
            writer.writerow(row)
    return p
