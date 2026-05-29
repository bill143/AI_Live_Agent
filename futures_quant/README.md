# futures_quant

A futures research & execution system for **NQ / MNQ** (CME e-mini / micro
e-mini Nasdaq-100 futures), hosted on the NautilusTrader engine.

> **Where this lives.** This package is developed inside the `AI_Live_Agent`
> repository at the operator's explicit direction. It is fully self-contained
> under `futures_quant/` and does **not** touch the surrounding LiveKit Agents
> code, its `pyproject.toml`, or its `makefile`. It is intended to be lifted
> into a dedicated repo (`futures-quant`) later.

---

## Read this first — operating constraints (non-negotiable)

These hold in every phase. They are enforced in code, not just promised:

- **Backtest / paper is the default.** Live execution is built but **disabled**
  behind an explicit, human-approved flag, granted *per phase*. See
  `config/default.yaml` → `live_enabled: false`.
- **No look-ahead bias.** Historical data is exposed through an *as-of* access
  API (`data/asof.py`) that *structurally cannot* return a bar that closed
  after the query time. It is impossible to read bar `t+1` while asking for
  data as of `t`.
- **No survivorship / no hidden back-adjustment.** Contract rolls are
  **explicit and logged** (`data/roll.py`). We never silently stitch a
  back-adjusted continuous price series.
- **No mock fills, no fake returns, no fabricated market data.** The loader
  operates only on a real export you provide. With no data present it fails
  loudly. (Unit-test fixtures use clearly-labelled synthetic bars to exercise
  the *validators* — never to produce returns or fills.)
- **All stubs throw loudly and are greppable.** Every not-yet-built component
  raises `StubNotImplementedError` (see `exceptions.py`), whose message carries
  the marker `STUB NOT IMPLEMENTED`. List every unbuilt call site statically
  with: `grep -rn "stub(" futures_quant --include=*.py`
- **Walk-forward validation is mandatory** before any config is called "best"
  (later phase).

---

## What's built (Phase 1) and what's a loud stub

Phase 1 = **foundation scaffold + historical data layer**. Nothing trades.

| Area | Status | Module |
|------|--------|--------|
| Instrument specs (NQ/MNQ) | ✅ built, real values | `instruments.py` |
| Canonical bar schema | ✅ built | `data/schema.py` |
| Data validation (no-look-ahead, tick grid, OHLC sanity, gaps) | ✅ built | `data/validation.py` |
| As-of access API (structural no-look-ahead) | ✅ built | `data/asof.py` |
| Explicit, logged contract roll | ✅ built | `data/roll.py` |
| NinjaTrader CSV ingest | ⏸ framework built, **fails loud until format pinned to a real sample** | `data/ninjatrader.py` |
| LSTM regime gate | 🚧 loud stub | `models/lstm_regime.py` |
| Kronos K-line forecast (feature only) | 🚧 loud stub | `models/kronos.py` |
| XGBoost signal model | 🚧 loud stub | `models/xgboost_signal.py` |
| Risk overlay (prop-firm rules, veto power) | 🚧 loud stub — **never silently stubbed in prod** | `risk/overlay.py` |
| Execution router (Tradovate/Lucid) | 🚧 loud stub, **disabled** | `execution/router.py` |
| Backtest engine (NautilusTrader host) | 🚧 loud stub | `backtest/engine.py` |
| Feature pipeline | 🚧 loud stub | `features/__init__.py` |
| Reports | 🚧 loud stub | `reports/__init__.py` |

---

## The one thing blocking the data loader

The **NinjaTrader → canonical adapter is intentionally not finished**, because
finishing it against guesses is exactly how a silent look-ahead / timezone bug
gets baked in. It will refuse to run until you confirm, from a *real* sample
export, three things (see `data/ninjatrader.py`):

1. **Timezone** of the export — exchange/Central Time vs your PC's local time.
2. **Timestamp edge** — does NinjaTrader stamp each 1-minute bar at its **open**
   or its **close**? (We canonicalise everything to the bar's **close** in UTC.)
3. **Header row** present or not, plus delimiter and column order.

Drop a few hundred rows of a real NQ export into `data/` with those three notes
beside it, and the adapter gets pinned in one pass.

---

## Data input contract (what a clean file looks like)

Per-delivery-month files (e.g. `NQH24`, `NQM24`, …), **1-minute** bars, **full
Globex / ETH** session. Canonical columns (after adaptation):

| column | meaning |
|--------|---------|
| `timestamp` | ISO-8601 **UTC**, the bar's **close** instant |
| `open` `high` `low` `close` | price in index points, on the 0.25 tick grid |
| `volume` | contracts traded in the bar (integer) |
| `symbol` | `NQ` or `MNQ` |
| `contract` | delivery month, e.g. `NQH24` |

---

## Running things

Dependency-free (Python ≥ 3.10 standard library only).

```bash
# Run the Phase 1 test suite (validators, as-of API, roll, schema)
python -m unittest discover -s futures_quant/tests -v

# Find every unbuilt component (they all throw loudly)
grep -rn "stub(" futures_quant --include=*.py
```
