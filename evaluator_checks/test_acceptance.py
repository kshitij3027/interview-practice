"""POST-PRACTICE ONLY evaluator smoke scenarios; run separately after implementation."""
import unittest
from freshclaim.catalog import Lot
from freshclaim.engine import FreshClaim


def lot(name, a, b, q):
    return Lot(name, "S", "K", a, b, q)


def request(*orders):
    return {"request_id":"case", "store_id":"S", "sku":"K", "orders":[{"order_id":name,"pickup_min":t,"units":q} for name,t,q in orders]}


class HiddenAcceptance(unittest.TestCase):
    def check(self, batches, orders, accepted, units):
        result = FreshClaim({("S","K"): batches}).assess(request(*orders))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["fulfilled_order_ids"], accepted)
        self.assertEqual(result["fulfilled_units"], units)
        self.assertEqual(result["unfilled_order_ids"], sorted({o[0] for o in orders} - set(accepted)))

    def test_full_orders_over_units(self):
        self.check([lot("L",0,10,10)], [("a",5,6),("b",5,5),("c",5,5)], ["b","c"],10)

    def test_exclusive_expiry_and_late_delivery(self):
        self.check([lot("A",0,4,4),lot("B",4,9,4)], [("a",2,4),("b",4,4)], ["a","b"],8)

    def test_later_only(self):
        self.check([lot("A",5,10,6)], [("earlier",4,6),("later",5,6)], ["later"],6)

    def test_units_second(self):
        self.check([lot("A",0,10,6)], [("a",3,3),("b",3,5)], ["b"],5)

    def test_lex_tie(self):
        self.check([lot("A",0,10,3)], [("z",3,3),("A",3,3)], ["A"],3)

    def test_zero_stock_empty(self):
        self.check([lot("A",0,10,0)], [("x",5,1)], [],0)
        self.check([lot("A",0,10,0)], [], [],0)


if __name__ == "__main__":
    unittest.main()
