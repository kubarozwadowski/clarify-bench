import unittest
from pricing import round_price
class FinalChecks(unittest.TestCase):
    def test_ties(self):
        for value, expected in (("1.005","1.00"),("1.015","1.02"),("2.685","2.68"),("-1.005","-1.00"),("-1.015","-1.02")):
            with self.subTest(value=value): self.assertEqual(round_price(value), expected)
    def test_non_ties(self):
        for value, expected in (("1.0049","1.00"),("1.0051","1.01"),("-1.0051","-1.01"),("9.999","10.00"),("123456789012.345001","123456789012.35")):
            with self.subTest(value=value): self.assertEqual(round_price(value), expected)
    def test_formatting(self):
        for value, expected in (("0","0.00"),("-0.001","0.00"),("-0.000","0.00"),("2","2.00"),("+4.5","4.50")):
            with self.subTest(value=value): self.assertEqual(round_price(value), expected)
