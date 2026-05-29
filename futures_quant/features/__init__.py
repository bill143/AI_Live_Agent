"""Feature pipeline (Phase 2).

Computes the inputs the models consume — including the Kronos forecast, which
enters here strictly as a *feature*, never as a direct trade signal. Every
feature must be computed through the as-of API so it can only use information
knowable at the bar it is attached to.
"""

from __future__ import annotations

from ..data.asof import AsOfSeries
from ..exceptions import stub


def build_features(series: AsOfSeries) -> object:
    """Build the model feature matrix from validated, as-of bar data."""
    stub("features.build_features", phase="Phase 2 (feature engineering)")
