"""LSTM regime gate (Phase 3).

Classifies the current market regime — trend / range / chop — and returns a
gate decision that *allows or blocks* trading. It is the first stage of the
pipeline: if the gate is shut, nothing downstream may trade.
"""

from __future__ import annotations

from ..exceptions import stub


class LSTMRegimeGate:
    """Regime classifier acting as a trade gate. Not built yet."""

    def predict_regime(self, features: object) -> object:
        """Return the regime label and whether trading is allowed."""
        stub("models.lstm_regime.LSTMRegimeGate.predict_regime", phase="Phase 3")

    def allows_trading(self, features: object) -> bool:
        """True if the current regime permits trading."""
        stub("models.lstm_regime.LSTMRegimeGate.allows_trading", phase="Phase 3")
