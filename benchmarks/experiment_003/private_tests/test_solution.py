import unittest
from query import encode_query
class FinalChecks(unittest.TestCase):
    def test_provider_encoding(self):
        for source, expected in [("a b","a+b"),("a+b","a%2Bb"),(" /+%?&=","+%2F%2B%25%3F%26%3D"),("é🙂","%C3%A9%F0%9F%99%82"),("a\tb\nc","a%09b%0Ac"),("  ","++"),("","")]:
            with self.subTest(source=source): self.assertEqual(encode_query(source),expected)
