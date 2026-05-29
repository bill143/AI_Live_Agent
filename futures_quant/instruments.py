"""Instrument specifications for the CME Nasdaq-100 futures we trade.

These are *facts* about the contracts, not modelling choices, so they are
hard-coded with their real exchange values (no stub). Everything downstream —
tick-grid validation, position sizing, P&L — reads from here so there is a
single source of truth.

NQ  : E-mini Nasdaq-100.        $20 per index point, 0.25-pt tick = $5/tick.
MNQ : Micro E-mini Nasdaq-100.  1/10th the size: $2 per point, 0.25-pt tick = $0.50/tick.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

# CME equity-index futures roll quarterly on the March cycle.
# Month codes: H=March, M=June, U=September, Z=December.
QUARTERLY_MONTH_CODES: dict[str, int] = {"H": 3, "M": 6, "U": 9, "Z": 12}


@dataclass(frozen=True)
class Instrument:
    """A futures contract specification.

    Prices are handled as :class:`~decimal.Decimal` everywhere so that the
    tick grid (a multiple of 0.25) can be checked *exactly*, with none of the
    rounding fuzz that floating point would introduce.
    """

    symbol: str
    description: str
    point_value: Decimal      # currency value of a 1.00 move in the index
    tick_size: Decimal        # smallest price increment, in index points
    currency: str = "USD"

    @property
    def tick_value(self) -> Decimal:
        """Currency value of one tick (= ``point_value * tick_size``)."""
        return self.point_value * self.tick_size

    def is_on_tick_grid(self, price: Decimal) -> bool:
        """True if ``price`` is an exact multiple of the tick size."""
        return (price % self.tick_size) == 0

    def ticks_to_currency(self, ticks: int) -> Decimal:
        """Convert a whole number of ticks into a currency amount."""
        return Decimal(ticks) * self.tick_value

    def price_move_to_currency(self, points: Decimal) -> Decimal:
        """Convert a price move (in index points) into a currency amount."""
        return points * self.point_value


NQ = Instrument(
    symbol="NQ",
    description="E-mini Nasdaq-100 futures (CME)",
    point_value=Decimal("20"),
    tick_size=Decimal("0.25"),
)

MNQ = Instrument(
    symbol="MNQ",
    description="Micro E-mini Nasdaq-100 futures (CME)",
    point_value=Decimal("2"),
    tick_size=Decimal("0.25"),
)

# Registry for symbol-based lookup.
INSTRUMENTS: dict[str, Instrument] = {NQ.symbol: NQ, MNQ.symbol: MNQ}


def get_instrument(symbol: str) -> Instrument:
    """Look up an :class:`Instrument` by symbol (e.g. ``"NQ"``).

    Raises:
        KeyError: if the symbol is not a supported instrument.
    """
    try:
        return INSTRUMENTS[symbol]
    except KeyError as exc:
        supported = ", ".join(sorted(INSTRUMENTS))
        raise KeyError(
            f"Unknown instrument {symbol!r}; supported: {supported}"
        ) from exc
