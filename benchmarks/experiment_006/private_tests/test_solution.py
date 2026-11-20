import unittest
from sorting import sort_names
class FinalChecks(unittest.TestCase):
    def test_casefold_and_stability(self):
        for names, expected in [(["Z","a","B"],["a","B","Z"]),(["b","A","a","B"],["A","a","b","B"]),(["Straße","STRASSE","strasse","apple"],["apple","Straße","STRASSE","strasse"]),(["a","a","A"],["a","a","A"]),(["é","Z","a"],["a","Z","é"]),([],[])]:
            with self.subTest(names=names):
                before = names[:]
                result = sort_names(names)
                self.assertEqual(result,expected)
                self.assertEqual(names,before)
                self.assertIsNot(result,names)
