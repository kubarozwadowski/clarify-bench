import unittest
from quantities import clamp_quantity
class SmokeChecks(unittest.TestCase):
    def test_inside_bounds(self):
        self.assertEqual(clamp_quantity(7), 7)
    def test_below_default(self):
        self.assertEqual(clamp_quantity(0), 1)
