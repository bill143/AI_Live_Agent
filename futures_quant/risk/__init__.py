"""Risk overlay package.

Enforces prop-firm rules (Lucid-style EOD drawdown, position sizing, max daily
loss, hard stop) and holds VETO power over any model signal. This component is
production-grade by mandate and must NEVER be silently stubbed in a live path —
the Phase 1 stub throws loudly precisely so it cannot be mistaken for working.
"""

from __future__ import annotations
