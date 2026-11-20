from datetime import date, timedelta
import unittest
from reminders import reminder_date
class SmokeChecks(unittest.TestCase):
    def test_weekdays(self):
        monday = date(2026,11,16)
        for days in range(5):
            value = monday+timedelta(days=days)
            self.assertEqual(reminder_date(value),value)
