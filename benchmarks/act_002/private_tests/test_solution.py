import unittest
from quantities import clamp_quantity
class FinalChecks(unittest.TestCase):
    def test_default_boundaries(self):
        for value, expected in ((-50,1),(0,1),(1,1),(2,2),(98,98),(99,99),(100,99),(10**30,99)):
            with self.subTest(value=value): self.assertEqual(clamp_quantity(value), expected)
    def test_custom_and_equal_bounds(self):
        for value, low, high, expected in ((-9,-5,-2,-5),(-3,-5,-2,-3),(0,-5,-2,-2),(100,4,4,4),(-2,4,4,4),(0,-1,1,0)):
            with self.subTest(value=value,low=low,high=high): self.assertEqual(clamp_quantity(value,low,high),expected)
    def test_invalid_order(self):
        for value in (-100,0,100):
            with self.assertRaises(ValueError): clamp_quantity(value,5,2)
