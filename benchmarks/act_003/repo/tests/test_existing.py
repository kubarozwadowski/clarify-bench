import unittest
from labels import unique_labels
class SmokeChecks(unittest.TestCase):
    def test_first_occurrence(self):
        self.assertEqual(unique_labels(["bug","feature","bug"]),["bug","feature"])
    def test_empty(self):
        self.assertEqual(unique_labels([]),[])
