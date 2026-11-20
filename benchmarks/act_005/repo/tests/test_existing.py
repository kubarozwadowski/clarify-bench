import unittest
from retry import should_retry
class SmokeChecks(unittest.TestCase):
    def test_service_failure(self):
        self.assertIs(should_retry(503,0),True)
    def test_success(self):
        self.assertIs(should_retry(200,0),False)
