"""The three-model pipeline: LSTM regime gate → Kronos feature → XGBoost signal.

Order matters and is enforced downstream:
  1. LSTM decides the regime (trend/range/chop) and *allows or blocks* trading.
  2. Kronos forecasts K-lines; its output is a FEATURE only, never a trade.
  3. XGBoost makes the long/short/flat call with a confidence score.

All three are loud stubs in Phase 1.
"""

from __future__ import annotations
