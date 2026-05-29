"""Canonical bar schema.

A :class:`Bar` is one OHLCV bar in the canonical form the whole system speaks.
Vendor adapters (e.g. NinjaTrader) convert *into* this; validators and the
as-of API operate *on* this.

Conventions baked in here — chosen to head off the classic look-ahead and
timezone bugs:

  * ``ts`` is the bar's **close** instant, timezone-aware, in **UTC**. A bar is
    only knowable at or after this moment.
  * prices are :class:`~decimal.Decimal` so tick-grid checks are exact.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator, Sequence

from ..exceptions import DataValidationError

# The canonical CSV header, in order. Adapters must emit exactly this.
CANONICAL_COLUMNS: tuple[str, ...] = (
    "timestamp",  # ISO-8601 UTC, bar CLOSE instant
    "open",
    "high",
    "low",
    "close",
    "volume",
    "symbol",
    "contract",
)


@dataclass(frozen=True)
class Bar:
    """One canonical OHLCV bar.

    Attributes:
        ts: bar CLOSE instant, timezone-aware UTC.
        open, high, low, close: prices in index points (Decimal).
        volume: contracts traded during the bar.
        symbol: instrument symbol, e.g. ``"NQ"``.
        contract: delivery-month contract, e.g. ``"NQH24"``.
    """

    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    symbol: str
    contract: str

    def __post_init__(self) -> None:
        # A bar with a naive (tz-unaware) timestamp is the single most
        # dangerous thing we can let through, so reject it at construction.
        if self.ts.tzinfo is None or self.ts.utcoffset() is None:
            raise DataValidationError(
                f"Bar timestamp {self.ts!r} is timezone-naive; canonical bars "
                f"must be timezone-aware UTC."
            )
        if self.ts.utcoffset() != timezone.utc.utcoffset(None):
            raise DataValidationError(
                f"Bar timestamp {self.ts!r} is not in UTC; canonicalise the "
                f"vendor timezone to UTC before constructing a Bar."
            )


def _parse_decimal(field: str, value: str, *, line: int) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise DataValidationError(
            f"Row {line}: column {field!r} value {value!r} is not a valid decimal."
        ) from exc


def parse_row(row: dict[str, str], *, line: int) -> Bar:
    """Parse one canonical CSV row (as a dict) into a :class:`Bar`.

    Raises:
        DataValidationError: if any field is missing or malformed.
    """
    missing = [c for c in CANONICAL_COLUMNS if c not in row]
    if missing:
        raise DataValidationError(
            f"Row {line}: missing required column(s): {', '.join(missing)}."
        )

    ts_raw = row["timestamp"].strip()
    try:
        # Accept a trailing 'Z' as UTC (datetime.fromisoformat handles it from
        # Python 3.11, but normalise defensively for older inputs).
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DataValidationError(
            f"Row {line}: timestamp {ts_raw!r} is not valid ISO-8601."
        ) from exc

    try:
        volume = int(row["volume"])
    except ValueError as exc:
        raise DataValidationError(
            f"Row {line}: volume {row['volume']!r} is not an integer."
        ) from exc

    return Bar(
        ts=ts,
        open=_parse_decimal("open", row["open"].strip(), line=line),
        high=_parse_decimal("high", row["high"].strip(), line=line),
        low=_parse_decimal("low", row["low"].strip(), line=line),
        close=_parse_decimal("close", row["close"].strip(), line=line),
        volume=volume,
        symbol=row["symbol"].strip(),
        contract=row["contract"].strip(),
    )


def read_canonical_csv(path: str | Path) -> list[Bar]:
    """Read a canonical CSV file into a list of :class:`Bar`.

    This reads *canonical* files (already adapted from a vendor format). It does
    not validate ordering / gaps / tick grid — that is the validator's job —
    but it does fail loudly on structural/parse errors.
    """
    p = Path(path)
    if not p.exists():
        raise DataValidationError(
            f"No data file at {p}. The loader never fabricates bars; drop a "
            f"real export in place."
        )

    with p.open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise DataValidationError(f"{p} is empty (no header row).")
        header = tuple(name.strip() for name in reader.fieldnames)
        if header != CANONICAL_COLUMNS:
            raise DataValidationError(
                f"{p} header {header} does not match canonical schema "
                f"{CANONICAL_COLUMNS}."
            )
        return [parse_row(row, line=i) for i, row in enumerate(reader, start=2)]


def iter_canonical_header() -> Iterator[str]:
    """Yield the canonical column names (helper for adapters writing output)."""
    yield from CANONICAL_COLUMNS


def to_csv_rows(bars: Sequence[Bar]) -> Iterator[list[str]]:
    """Render bars back to canonical CSV rows (header first). Used by adapters."""
    yield list(CANONICAL_COLUMNS)
    for b in bars:
        yield [
            b.ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            str(b.open),
            str(b.high),
            str(b.low),
            str(b.close),
            str(b.volume),
            b.symbol,
            b.contract,
        ]
