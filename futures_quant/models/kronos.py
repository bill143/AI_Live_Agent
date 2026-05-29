"""Kronos K-line forecasting model (Phase 4).

Kronos is a foundation model for K-line (candlestick) forecasting. Its output
is consumed by the feature pipeline and becomes an INPUT FEATURE to the XGBoost
signal model. It must never place or directly determine a trade on its own.
"""

from __future__ import annotations

from ..exceptions import stub


class KronosForecaster:
    """K-line forecaster. Output is a feature only. Not built yet."""

    def forecast(self, features: object) -> object:
        """Produce a K-line forecast to be used downstream as a feature."""
        stub("models.kronos.KronosForecaster.forecast", phase="Phase 4")
