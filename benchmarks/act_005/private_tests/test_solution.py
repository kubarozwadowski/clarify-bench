import unittest
from retry import should_retry
class FinalChecks(unittest.TestCase):
    def test_all_codes_and_budget_boundaries(self):
        for status in range(100,600):
            for used in (0,1,2,3,4,100):
                with self.subTest(status=status,used=used):
                    self.assertIs(should_retry(status,used),(status==429 or 500<=status<=599) and used<3)
