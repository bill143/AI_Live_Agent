"""Shared test helpers: synthetic bar construction.

SYNTHETIC DATA NOTICE: bars built here are hand-crafted fixtures used solely to
exercise validation / as-of / roll logic. They are not market data and must
never feed a backtest or produce returns.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from futures_quant.data.schema import Bar

_BASE = datetime(2024, 3, 1, 0, 0, tzinfo=timezone.utc)


def bar(
    minute: int,
    *,
    o: str = "18000.00",
    h: str = "18001.00",
    l: str = "17999.00",
    c: str = "18000.25",
    volume: int = 100,
    symbol: str = "NQ",
    contract: str = "NQH24",
    base: datetime = _BASE,
) -> Bar:
    """Build a synthetic, tick-grid-valid bar at ``base + minute`` minutes."""
    return Bar(
        ts=base + timedelta(minutes=minute),
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(l),
        close=Decimal(c),
        volume=volume,
        symbol=symbol,
        contract=contract,
    )


def consecutive(n: int, *, contract: str = "NQH24", base: datetime = _BASE) -> list[Bar]:
    """Build ``n`` consecutive 1-minute bars."""
    return [bar(i, contract=contract, base=base) for i in range(n)]
