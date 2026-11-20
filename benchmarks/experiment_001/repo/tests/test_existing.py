import unittest
from pricing import round_price
class SmokeChecks(unittest.TestCase):
    def test_exact_price(self):
        self.assertEqual(round_price("12.34"), "12.34")
    def test_two_places(self):
        self.assertEqual(round_price("2"), "2.00")
