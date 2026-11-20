import unittest
from query import encode_query
class SmokeChecks(unittest.TestCase):
    def test_unreserved_ascii(self):
        self.assertEqual(encode_query("abcXYZ019-._~"),"abcXYZ019-._~")
    def test_empty(self):
        self.assertEqual(encode_query(""),"")
