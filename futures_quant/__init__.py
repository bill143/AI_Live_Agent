"""futures_quant — futures research & execution system for NQ / MNQ.

Phase 1 scope: foundation scaffold + historical data layer. Nothing trades.
Every not-yet-built component raises ``StubNotImplementedError`` (see
``futures_quant.exceptions``); list them with ``grep -rn "stub(" futures_quant``.

Operating constraints are enforced in code, not merely documented:
  * backtest/paper is the default; live execution is gated behind an explicit,
    human-approved per-phase flag;
  * historical data is exposed only through an as-of API that cannot return a
    bar which closed after the query time (no look-ahead);
  * contract rolls are explicit and logged (no hidden back-adjustment);
  * no fabricated market data, mock fills, or fake returns.
"""

from __future__ import annotations

__version__ = "0.1.0"
