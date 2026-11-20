import unittest
from accounts import create_account
class SmokeChecks(unittest.TestCase):
    def test_record_shape(self):
        record = create_account("u1","ada@example.test")
        self.assertEqual(set(record),{"id","email","product_notifications"})
        self.assertEqual(record["id"],"u1")
        self.assertEqual(record["email"],"ada@example.test")
        self.assertIs(type(record["product_notifications"]),bool)
