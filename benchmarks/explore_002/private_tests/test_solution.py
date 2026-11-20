import copy
from datetime import datetime, timedelta, timezone
import unittest
from serializers import serialize_event
class FinalChecks(unittest.TestCase):
    def test_timestamp_convention(self):
        cases = [(datetime(2026,6,1,13,2,3,tzinfo=timezone.utc),"2026-06-01T13:02:03Z"),
                 (datetime(2026,1,1,1,2,3,999999,tzinfo=timezone(timedelta(hours=5,minutes=30))),"2025-12-31T19:32:03Z"),
                 (datetime(2025,12,31,23,30,tzinfo=timezone(timedelta(hours=-4))),"2026-01-01T03:30:00Z")]
        for instant, expected in cases:
            with self.subTest(instant=instant):
                record = {"id":"e1", "starts_at":instant, "title":"Unused"}
                before = copy.deepcopy(record)
                self.assertEqual(serialize_event(record), {"id":"e1", "starts_at":expected})
                self.assertEqual(record,before)
