import unittest
from sorting import sort_names
class SmokeChecks(unittest.TestCase):
    def test_lowercase_names(self):
        names = ["pear","apple","banana"]
        self.assertEqual(sort_names(names),["apple","banana","pear"])
        self.assertEqual(names,["pear","apple","banana"])
    def test_empty(self):
        names = []
        result = sort_names(names)
        self.assertEqual(result,[])
        self.assertIsNot(result,names)
