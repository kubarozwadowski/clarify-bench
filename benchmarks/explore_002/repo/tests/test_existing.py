from datetime import datetime, timedelta, timezone
import unittest
from serializers import serialize_meeting, serialize_deadline
class ExistingBehavior(unittest.TestCase):
    def test_meeting(self):
        record = {"id":"m1", "starts_at":datetime(2026,1,2,12,30,0,123456,tzinfo=timezone(timedelta(hours=2)))}
        self.assertEqual(serialize_meeting(record), {"id":"m1", "starts_at":"2026-01-02T10:30:00Z"})
    def test_deadline(self):
        record = {"id":"d1", "due_at":datetime(2026,1,2,tzinfo=timezone.utc)}
        self.assertEqual(serialize_deadline(record), {"id":"d1", "due_at":"2026-01-02T00:00:00Z"})
