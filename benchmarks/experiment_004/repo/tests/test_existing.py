import unittest
from timestamps import encode_timestamp
class SmokeChecks(unittest.TestCase):
    def test_epoch(self):
        value = encode_timestamp("1970-01-01T00:00:00Z")
        self.assertIs(type(value),int)
        self.assertEqual(value,0)
