"""Historical market-data layer.

This is the foundation everything downstream trusts, so it is built and tested
before any model exists. Its job:

  * define the canonical bar schema (:mod:`futures_quant.data.schema`);
  * validate input loudly — never silently repair (:mod:`futures_quant.data.validation`);
  * expose data only through an as-of API that cannot leak the future
    (:mod:`futures_quant.data.asof`);
  * handle contract rolls explicitly and with a log (:mod:`futures_quant.data.roll`);
  * adapt vendor exports into the canonical schema — refusing to guess at the
    vendor format (:mod:`futures_quant.data.ninjatrader`).
"""

from __future__ import annotations
