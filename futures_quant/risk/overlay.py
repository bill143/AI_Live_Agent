"""Risk overlay with veto power (Phase 6).

Sits between the signal model and execution. It enforces the prop-firm rule set
and can VETO any signal — flattening or blocking — regardless of model
confidence. Rules include the Lucid end-of-day drawdown model, per-trade and
aggregate position sizing, max daily loss, and a hard stop.

Mandate: production-grade, never stubbed in a live path. The stub below throws
loudly so an unbuilt overlay can never be mistaken for an approving one.
"""

from __future__ import annotations

from ..config import RiskConfig
from ..exceptions import stub


class RiskOverlay:
    """Prop-firm risk enforcement with veto authority. Not built yet."""

    def __init__(self, config: RiskConfig) -> None:
        self._config = config

    def review(self, signal: object, account_state: object) -> object:
        """Approve, resize, or VETO a signal against the prop-firm rule set.

        A real implementation must default to *deny* on any uncertainty.
        """
        stub("risk.overlay.RiskOverlay.review", phase="Phase 6 (risk overlay)")
