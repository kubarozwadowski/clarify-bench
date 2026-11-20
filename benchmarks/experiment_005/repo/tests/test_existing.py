import unittest
from messages import chunk_message
class SmokeChecks(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(chunk_message("abcdefghijk"),["abcdefgh","ijk"])
    def test_empty(self):
        self.assertEqual(chunk_message(""),[])
