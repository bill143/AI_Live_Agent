"""Phase 1 test suite for futures_quant.

These tests exercise the data layer's correctness guarantees. Test fixtures use
clearly-synthetic bars to drive the *validators* and the as-of API — they are
never used to produce returns or fills. Run with::

    python -m unittest discover -s futures_quant/tests -v
"""

from __future__ import annotations
