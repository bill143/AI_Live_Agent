"""Data validation — loud failure, never silent repair.

Validation splits into two severities:

* **Hard errors** raise :class:`DataValidationError` immediately. These are
  conditions under which the data is untrustworthy and nothing downstream
  should run: timestamps out of order or duplicated, OHLC that is internally
  impossible, prices off the tick grid, negative volume.

* **Gaps** are *reported*, not raised. Real Globex data has legitimate gaps
  (the daily maintenance halt, holidays). We surface every gap as structured
  data so the operator can eyeball it, but we never silently invent bars to
  fill one. The precise session calendar gets pinned alongside the first real
  sample; until then a gap is simply "more than one bar interval between
  consecutive bars."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Sequence

from ..exceptions import DataValidationError
from ..instruments import get_instrument
from .schema import Bar


@dataclass(frozen=True)
class Gap:
    """A reported (non-fatal) gap between two consecutive bars."""

    prev_ts: datetime
    next_ts: datetime
    missing_intervals: int  # how many bar-intervals are absent in the gap


@dataclass
class ValidationReport:
    """Outcome of validating a single contract's bars."""

    contract: str
    n_bars: int
    gaps: list[Gap] = field(default_factory=list)

    @property
    def has_gaps(self) -> bool:
        return bool(self.gaps)

    def summary(self) -> str:
        return (
            f"{self.contract}: {self.n_bars} bars, {len(self.gaps)} gap(s) "
            f"reported (not filled)."
        )


def _check_ohlc_sane(bar: Bar, *, index: int) -> None:
    hi, lo = bar.high, bar.low
    o, c = bar.open, bar.close
    if hi < lo:
        raise DataValidationError(
            f"Bar #{index} ({bar.ts.isoformat()}): high {hi} < low {lo}."
        )
    if hi < max(o, c) or lo > min(o, c):
        raise DataValidationError(
            f"Bar #{index} ({bar.ts.isoformat()}): OHLC inconsistent "
            f"(o={o}, h={hi}, l={lo}, c={c}); high must be the max and low the min."
        )
    if bar.volume < 0:
        raise DataValidationError(
            f"Bar #{index} ({bar.ts.isoformat()}): negative volume {bar.volume}."
        )


def _check_tick_grid(bar: Bar, *, index: int) -> None:
    inst = get_instrument(bar.symbol)
    for name, price in (("open", bar.open), ("high", bar.high),
                        ("low", bar.low), ("close", bar.close)):
        if not inst.is_on_tick_grid(price):
            raise DataValidationError(
                f"Bar #{index} ({bar.ts.isoformat()}): {name} price {price} is "
                f"off the {inst.symbol} tick grid (tick size {inst.tick_size})."
            )


def validate_bars(
    bars: Sequence[Bar],
    *,
    contract: str,
    bar_interval: timedelta = timedelta(minutes=1),
) -> ValidationReport:
    """Validate one contract's bars, returning a :class:`ValidationReport`.

    Raises:
        DataValidationError: on any hard error (ordering, duplication,
            tick-grid, OHLC sanity, negative volume, mixed contract/symbol).
    """
    if not bars:
        raise DataValidationError(
            f"{contract}: no bars to validate; refusing to proceed on empty data."
        )

    report = ValidationReport(contract=contract, n_bars=len(bars))
    prev: Bar | None = None

    for i, bar in enumerate(bars):
        if bar.contract != contract:
            raise DataValidationError(
                f"Bar #{i}: contract {bar.contract!r} does not match expected "
                f"{contract!r}; do not mix contracts in one series."
            )

        _check_ohlc_sane(bar, index=i)
        _check_tick_grid(bar, index=i)

        if prev is not None:
            if bar.ts <= prev.ts:
                # Duplicate or backwards timestamp: this is how look-ahead and
                # double-counting creep in. Fatal.
                raise DataValidationError(
                    f"Bar #{i}: timestamp {bar.ts.isoformat()} is not strictly "
                    f"after the previous {prev.ts.isoformat()}; timestamps must "
                    f"be unique and ascending."
                )
            delta = bar.ts - prev.ts
            if delta > bar_interval:
                missing = int(delta / bar_interval) - 1
                report.gaps.append(
                    Gap(prev_ts=prev.ts, next_ts=bar.ts, missing_intervals=missing)
                )
        prev = bar

    return report
