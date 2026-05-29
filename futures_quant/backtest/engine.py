"""NautilusTrader-hosted backtest engine (Phase 8).

Wires the validated data layer, feature pipeline, three-model stack, and risk
overlay into a NautilusTrader backtest. The same strategy code runs live, so
results carry over with code parity. No mock fills, no fabricated returns —
fills come from the engine's matching against real historical bars.
"""

from __future__ import annotations

from ..config import Config
from ..exceptions import stub


class BacktestEngine:
    """Event-driven backtest host. Not built yet."""

    def __init__(self, config: Config) -> None:
        config.assert_safe_for_phase1()
        self._config = config

    def run(self) -> object:
        """Run the backtest and return validated performance results."""
        stub("backtest.engine.BacktestEngine.run", phase="Phase 8 (backtest engine)")
