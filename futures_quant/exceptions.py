"""Exception types for futures_quant.

Two design rules live here:

1. **Stubs are loud and greppable.** Anything not yet built calls
   :func:`stub`, which raises :class:`StubNotImplementedError` carrying the
   marker string ``STUB NOT IMPLEMENTED``. Find every unbuilt component with::

       grep -rn "STUB NOT IMPLEMENTED" futures_quant

2. **Data problems fail loudly.** The data layer never silently drops, fills,
   or "fixes" bad input. It raises :class:`DataValidationError` (or, for the
   look-ahead guarantee, :class:`LookAheadError`) so a problem cannot pass
   downstream unnoticed.
"""

from __future__ import annotations

from typing import NoReturn

# Marker embedded in every stub message so the whole codebase can be swept
# with a single grep. Do not change this string casually — tooling greps it.
STUB_MARKER = "STUB NOT IMPLEMENTED"


class FuturesQuantError(Exception):
    """Base class for all errors raised by this package."""


class StubNotImplementedError(FuturesQuantError, NotImplementedError):
    """Raised by any component that has been scaffolded but not yet built.

    Subclasses :class:`NotImplementedError` so it also trips generic
    "not implemented" handling, while remaining catchable as a
    :class:`FuturesQuantError`.
    """


class DataValidationError(FuturesQuantError):
    """Raised when input market data violates the canonical contract.

    The data layer treats any contract violation as fatal rather than
    silently repairing it, so a malformed or suspicious file can never be
    laundered into a backtest.
    """


class LookAheadError(FuturesQuantError):
    """Raised when code attempts to access data that is not yet knowable.

    This is the programmatic backstop behind the as-of access API: if a query
    would expose a bar that closed after the as-of timestamp, we raise rather
    than return it.
    """


class FormatNotConfirmedError(FuturesQuantError):
    """Raised when a vendor adapter is asked to parse before its real-world
    format has been confirmed against an actual sample file.

    Exists specifically to prevent the classic failure mode of building a
    loader against *guessed* delimiter / timezone / timestamp conventions.
    """


def stub(component: str, *, phase: str = "a later phase") -> NoReturn:
    """Raise a loud, greppable :class:`StubNotImplementedError`.

    Args:
        component: human-readable name of the unbuilt component.
        phase: when it is scheduled to be built, for the operator's benefit.

    Raises:
        StubNotImplementedError: always.
    """
    raise StubNotImplementedError(
        f"{STUB_MARKER}: {component} is not built yet (scheduled for {phase}). "
        f"It must throw rather than return a fabricated result."
    )
