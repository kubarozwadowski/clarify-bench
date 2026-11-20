import unittest
from labels import unique_labels
class FinalChecks(unittest.TestCase):
    def test_order_and_exact_matching(self):
        for source, expected in [(["b","a","b","c","a"],["b","a","c"]),(["Bug","bug","Bug"],["Bug","bug"]),(["","x","","x"],["","x"]),(["é","e","é","🙂","🙂"],["é","e","🙂"]),(["a"]*10,["a"]),([],[])]:
            with self.subTest(source=source):
                before = source[:]
                result = unique_labels(source)
                self.assertEqual(result,expected)
                self.assertEqual(source,before)
                self.assertIsNot(result,source)
