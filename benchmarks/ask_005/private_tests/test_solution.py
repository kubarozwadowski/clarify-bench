from datetime import date, timedelta
import unittest
from reminders import reminder_date
class FinalChecks(unittest.TestCase):
    def test_whole_week(self):
        monday = date(2026,11,16)
        for days in range(7):
            value = monday+timedelta(days=days)
            expected = value if days<5 else monday+timedelta(days=7)
            result = reminder_date(value)
            self.assertIs(type(result),date)
            self.assertEqual(result,expected)
    def test_boundaries(self):
        for value, expected in ((date(2022,12,31),date(2023,1,2)),(date(2026,1,31),date(2026,2,2)),(date(2020,2,29),date(2020,3,2)),(date(2024,2,29),date(2024,2,29))):
            with self.subTest(value=value): self.assertEqual(reminder_date(value),expected)
