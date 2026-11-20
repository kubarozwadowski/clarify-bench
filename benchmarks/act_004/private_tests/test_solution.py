import copy
import unittest
from orders import order_total
class FinalChecks(unittest.TestCase):
    def test_totals_and_preservation(self):
        for lines, expected in [([],0),([{"unit_price_cents":199,"quantity":3},{"unit_price_cents":50,"quantity":2}],697),([{"unit_price_cents":0,"quantity":9},{"unit_price_cents":42,"quantity":0}],0),([{"unit_price_cents":10**25,"quantity":10**10}],10**35)]:
            with self.subTest(lines=lines):
                before = copy.deepcopy(lines)
                result = order_total(lines)
                self.assertIs(type(result),int)
                self.assertEqual(result,expected)
                self.assertEqual(lines,before)
    def test_negative_values(self):
        for price, quantity in ((-1,1),(1,-1),(-1,0),(0,-1),(-1,-1)):
            with self.subTest(price=price,quantity=quantity):
                with self.assertRaises(ValueError):
                    order_total([{"unit_price_cents":100,"quantity":1},{"unit_price_cents":price,"quantity":quantity}])
