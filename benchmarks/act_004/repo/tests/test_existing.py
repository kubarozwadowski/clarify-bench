import unittest
from orders import order_total
class SmokeChecks(unittest.TestCase):
    def test_one_line(self):
        self.assertEqual(order_total([{"unit_price_cents":125,"quantity":2}]),250)
    def test_empty(self):
        self.assertEqual(order_total([]),0)
