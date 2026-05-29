from __future__ import annotations

import unittest
from decimal import Decimal

from futures_quant.instruments import MNQ, NQ, get_instrument


class TestInstruments(unittest.TestCase):
    def test_nq_values(self) -> None:
        self.assertEqual(NQ.point_value, Decimal("20"))
        self.assertEqual(NQ.tick_size, Decimal("0.25"))
        self.assertEqual(NQ.tick_value, Decimal("5.00"))

    def test_mnq_values(self) -> None:
        self.assertEqual(MNQ.point_value, Decimal("2"))
        self.assertEqual(MNQ.tick_size, Decimal("0.25"))
        self.assertEqual(MNQ.tick_value, Decimal("0.50"))

    def test_tick_grid(self) -> None:
        self.assertTrue(NQ.is_on_tick_grid(Decimal("18255.25")))
        self.assertFalse(NQ.is_on_tick_grid(Decimal("18255.30")))

    def test_price_move_to_currency(self) -> None:
        # A 10-point move on NQ = $200.
        self.assertEqual(NQ.price_move_to_currency(Decimal("10")), Decimal("200"))

    def test_lookup_unknown_raises(self) -> None:
        with self.assertRaises(KeyError):
            get_instrument("ES")


if __name__ == "__main__":
    unittest.main()
