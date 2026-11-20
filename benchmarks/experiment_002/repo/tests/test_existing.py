import unittest
from paging import cursor_after
class SmokeChecks(unittest.TestCase):
    def test_cursor_type_and_range(self):
        cursor = cursor_after(5)
        self.assertIs(type(cursor), int)
        self.assertGreaterEqual(cursor, 0)
