import unittest
from paging import cursor_after
class FinalChecks(unittest.TestCase):
    def test_minimal_cursor(self):
        for last_id in (0,1,2,5,6,9,12,13,10**18):
            with self.subTest(last_id=last_id):
                self.assertIs(type(cursor_after(last_id)), int)
                self.assertEqual(cursor_after(last_id), last_id + 1)
    def test_provider_integration(self):
        for ids in ([],[0],[2,5,9,12],[0,1,2,3],[100,101,1000]):
            for last_id in (0,1,2,5,6,12,100,1000):
                with self.subTest(ids=ids,last_id=last_id):
                    received = [i for i in ids if i >= cursor_after(last_id)]
                    self.assertEqual(received,[i for i in ids if i > last_id])
