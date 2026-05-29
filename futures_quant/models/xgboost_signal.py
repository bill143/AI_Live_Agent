"""XGBoost signal model (Phase 5).

The primary signal model. Consumes the full feature set (including the Kronos
forecast feature) and, only when the LSTM gate allows trading, emits the
long / short / flat decision together with a confidence score. Its output is
still subject to the risk overlay's veto before any order is considered.
"""

from __future__ import annotations

from ..exceptions import stub


class XGBoostSignalModel:
    """Long/short/flat signal with confidence. Not built yet."""

    def predict_signal(self, features: object) -> object:
        """Return the trade direction and a confidence score in [0, 1]."""
        stub("models.xgboost_signal.XGBoostSignalModel.predict_signal", phase="Phase 5")
