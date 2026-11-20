import unittest
from redaction import redact_record
class SmokeChecks(unittest.TestCase):
    def test_password(self):
        record = {"name":"Ada","password":"example-secret"}
        self.assertEqual(redact_record(record),{"name":"Ada","password":"[REDACTED]"})
        self.assertEqual(record["password"],"example-secret")
