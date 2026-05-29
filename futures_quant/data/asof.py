"""As-of access API — the structural no-look-ahead guarantee.

This is the piece that turns "don't peek at the future" from a convention
everyone *promises* to honour into something the code *cannot* violate.

An :class:`AsOfSeries` wraps an immutable, time-ordered list of bars. The only
way to read it is :meth:`AsOfSeries.as_of`, which returns the bars whose
**close** timestamp is at or before the query time. There is no method that
hands you "the next bar" or lets you index past the as-of horizon. A feature
computed at time ``t`` therefore physically cannot see bar ``t+1``.

Because every canonical :class:`Bar` is stamped at its close instant, "knowable
at time ``t``" is exactly "``bar.ts <= t``".
"""

from __future__ import annotations

import bisect
from datetime import datetime, timezone
from typing import Sequence

from ..exceptions import DataValidationError, LookAheadError
from .schema import Bar


class AsOfSeries:
    """Time-ordered, append-only-at-construction view over bars.

    The constructor verifies strict ascending order so that binary search over
    the close timestamps is sound. After construction the data is read-only.
    """

    __slots__ = ("_bars", "_close_ts")

    def __init__(self, bars: Sequence[Bar]) -> None:
        ordered = tuple(bars)
        for i in range(1, len(ordered)):
            if ordered[i].ts <= ordered[i - 1].ts:
                raise DataValidationError(
                    f"AsOfSeries requires strictly ascending timestamps; bar #{i} "
                    f"({ordered[i].ts.isoformat()}) is not after #{i - 1} "
                    f"({ordered[i - 1].ts.isoformat()}). Validate before wrapping."
                )
        self._bars: tuple[Bar, ...] = ordered
        # Parallel list of close timestamps for binary search.
        self._close_ts: list[datetime] = [b.ts for b in ordered]

    def __len__(self) -> int:
        return len(self._bars)

    @staticmethod
    def _require_aware(t: datetime) -> datetime:
        if t.tzinfo is None or t.utcoffset() is None:
            raise LookAheadError(
                f"as-of query time {t!r} is timezone-naive; pass a UTC-aware "
                f"datetime so the comparison is unambiguous."
            )
        return t.astimezone(timezone.utc)

    def as_of(self, t: datetime) -> tuple[Bar, ...]:
        """Return every bar knowable at time ``t`` (close timestamp ``<= t``).

        This is the *only* way to read the series. It cannot return a bar that
        closed after ``t``.
        """
        t = self._require_aware(t)
        # bisect_right gives the count of bars with close_ts <= t.
        idx = bisect.bisect_right(self._close_ts, t)
        return self._bars[:idx]

    def latest_as_of(self, t: datetime) -> Bar | None:
        """Return the most recent bar knowable at ``t``, or ``None`` if none."""
        window = self.as_of(t)
        return window[-1] if window else None

    def at_or_raise(self, t: datetime) -> Bar:
        """Return the bar whose close == ``t`` exactly, else raise.

        Guards against the subtle bug of treating "the bar at t" as knowable
        *before* it closes: only an exact close match is returned.
        """
        t = self._require_aware(t)
        idx = bisect.bisect_left(self._close_ts, t)
        if idx < len(self._close_ts) and self._close_ts[idx] == t:
            return self._bars[idx]
        raise LookAheadError(
            f"No bar closes exactly at {t.isoformat()}; refusing to return a "
            f"neighbouring bar, which would risk look-ahead."
        )

    def first_ts(self) -> datetime | None:
        return self._close_ts[0] if self._bars else None

    def last_ts(self) -> datetime | None:
        return self._close_ts[-1] if self._bars else None
