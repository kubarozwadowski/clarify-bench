from datetime import datetime, timezone
import unittest
from exports import export_rows
class SmokeChecks(unittest.TestCase):
    def test_shape(self):
        result = export_rows([{"id":"e1","starts_at":datetime(2026,6,1,12,tzinfo=timezone.utc)}])
        self.assertIsInstance(result,list)
        self.assertEqual(len(result),1)
        self.assertEqual(set(result[0]),{"id","starts_at"})
        self.assertEqual(result[0]["id"],"e1")
        self.assertRegex(result[0]["starts_at"],r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
    def test_empty(self):
        self.assertEqual(export_rows([]),[])
