"""Order router to Tradovate / Lucid (Phase 7).

Sends risk-approved orders to the live venue. This is the only component that
can move real money, so it carries a double safety gate: it is a loud stub in
Phase 1, AND it refuses to construct unless live execution has been explicitly
enabled in config. Both must change, deliberately, before anything routes.
"""

from __future__ import annotations

from ..config import Config
from ..exceptions import FuturesQuantError, stub


class LiveExecutionDisabledError(FuturesQuantError):
    """Raised when the router is created while live execution is disabled."""


class OrderRouter:
    """Routes approved orders to the configured venue. Not built yet."""

    def __init__(self, config: Config) -> None:
        # Safety gate #1: cannot even exist unless live execution is enabled.
        if not (config.live_enabled and config.execution.enabled):
            raise LiveExecutionDisabledError(
                "OrderRouter requires live_enabled and execution.enabled to both "
                "be true. Live routing is gated behind explicit per-phase approval; "
                "it stays off by default."
            )
        self._config = config

    def submit(self, order: object) -> object:
        """Submit a risk-approved order to the venue."""
        # Safety gate #2: even when enabled, the implementation is a loud stub.
        stub("execution.router.OrderRouter.submit", phase="Phase 7 (live execution)")
