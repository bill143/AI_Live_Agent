"""Explicit, logged contract roll.

NQ rolls quarterly (H/M/U/Z). To research across more than one contract we need
a single continuous series — but a *back-adjusted* continuous series is a
classic silent source of look-ahead and phantom price levels, so we do not
build one. Instead:

  * the active contract is chosen by an explicit, auditable policy;
  * every roll is recorded as a :class:`RollEvent` (when, from, to, why);
  * **prices are never back-adjusted** — each bar keeps its real traded price,
    and which contract it came from stays attached (``bar.contract``).

Two policies are provided:

  * :class:`CalendarRoll` — roll N exchange business days before expiry. Uses
    only information knowable at the bar's own time (the expiry date is known
    in advance), so it introduces no look-ahead.
  * :class:`VolumeRoll` — roll when the back contract's traded volume overtakes
    the front contract's, decided bar-by-bar using only data up to that bar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from ..exceptions import DataValidationError
from .schema import Bar


@dataclass(frozen=True)
class RollEvent:
    """A single roll from one contract to the next, with its reason."""

    ts: datetime
    from_contract: str
    to_contract: str
    reason: str


@dataclass(frozen=True)
class ContractSeries:
    """One contract's validated, time-ordered bars plus its expiry date."""

    contract: str
    expiry: date
    bars: tuple[Bar, ...]


class RollPolicy(Protocol):
    """Decides, at each step, whether to roll to the next contract."""

    def should_roll(self, bar: Bar, front: ContractSeries, back: ContractSeries) -> bool:
        ...

    @property
    def name(self) -> str:
        ...


@dataclass(frozen=True)
class CalendarRoll:
    """Roll ``days_before_expiry`` calendar days ahead of the front expiry.

    Note: uses calendar days for simplicity and determinism in Phase 1; an
    exchange-business-day calendar is pinned alongside the first real sample.
    """

    days_before_expiry: int = 5

    @property
    def name(self) -> str:
        return f"calendar(-{self.days_before_expiry}d)"

    def should_roll(self, bar: Bar, front: ContractSeries, back: ContractSeries) -> bool:
        days_to_expiry = (front.expiry - bar.ts.date()).days
        return days_to_expiry <= self.days_before_expiry


@dataclass(frozen=True)
class VolumeRoll:
    """Roll once the back contract trades more volume than the front.

    Decided per-bar using only data up to that bar, so no look-ahead. Requires
    aligned timestamps between the two contracts to compare like-for-like.
    """

    @property
    def name(self) -> str:
        return "volume-crossover"

    def should_roll(self, bar: Bar, front: ContractSeries, back: ContractSeries) -> bool:
        back_vol = _volume_at(back, bar.ts)
        return back_vol is not None and back_vol > bar.volume


def _volume_at(series: ContractSeries, ts: datetime) -> int | None:
    # Linear scan is fine for Phase 1 clarity; optimise later if needed.
    for b in series.bars:
        if b.ts == ts:
            return b.volume
    return None


@dataclass
class RollResult:
    """Continuous (non-adjusted) series plus the full roll log."""

    bars: list[Bar]
    events: list[RollEvent]

    def log_lines(self) -> list[str]:
        return [
            f"{e.ts.isoformat()}  ROLL {e.from_contract} -> {e.to_contract}  "
            f"({e.reason})"
            for e in self.events
        ]


def _first_roll_ts(front: ContractSeries, back: ContractSeries, policy: RollPolicy) -> datetime:
    """The instant the front contract rolls to the back, per ``policy``.

    Scans the front contract's bars in time order and returns the timestamp of
    the first bar that triggers the roll. If no bar triggers it (the front's
    data ends before the roll condition is met), we roll at the front's last
    bar so the series stays continuous — recorded with an explicit reason.
    """
    for bar in front.bars:
        if policy.should_roll(bar, front, back):
            return bar.ts
    return front.bars[-1].ts


def build_continuous(series: list[ContractSeries], policy: RollPolicy) -> RollResult:
    """Stitch ordered contracts into one continuous, **non-back-adjusted** series.

    Each contract contributes the bars inside a half-open time window:
    contract ``i`` owns ``[roll_in_i, roll_out_i)`` where ``roll_out_i`` is the
    instant it rolls to ``i+1`` (and ``roll_in_{i+1} == roll_out_i``). This
    windowing makes overlap impossible — every instant belongs to exactly one
    contract — and prices are copied through untouched (no back-adjustment).

    Args:
        series: contracts in chronological order of expiry (front first).
        policy: the roll decision policy.

    Raises:
        DataValidationError: if no contract is supplied, or expiries are not
            strictly increasing.
    """
    if not series:
        raise DataValidationError("build_continuous requires at least one contract.")
    for i in range(1, len(series)):
        if series[i].expiry <= series[i - 1].expiry:
            raise DataValidationError(
                f"Contracts must be ordered by strictly increasing expiry; "
                f"{series[i].contract} ({series[i].expiry}) does not follow "
                f"{series[i - 1].contract} ({series[i - 1].expiry})."
            )

    # Compute the roll instant out of each contract except the last.
    roll_out: list[datetime | None] = []
    events: list[RollEvent] = []
    for i in range(len(series) - 1):
        ts = _first_roll_ts(series[i], series[i + 1], policy)
        roll_out.append(ts)
        triggered = any(
            policy.should_roll(b, series[i], series[i + 1]) for b in series[i].bars
        )
        events.append(
            RollEvent(
                ts=ts,
                from_contract=series[i].contract,
                to_contract=series[i + 1].contract,
                reason=policy.name if triggered else f"{policy.name} (front exhausted)",
            )
        )
    roll_out.append(None)  # last contract has no roll-out

    out: list[Bar] = []
    roll_in: datetime | None = None  # contract 0 has no lower bound
    for i, contract in enumerate(series):
        lower, upper = roll_in, roll_out[i]
        for bar in contract.bars:
            if lower is not None and bar.ts < lower:
                continue
            if upper is not None and bar.ts >= upper:
                break
            out.append(bar)
        roll_in = roll_out[i]

    return RollResult(bars=out, events=events)
