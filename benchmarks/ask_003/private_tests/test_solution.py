import copy
from datetime import datetime, timezone
import unittest
from exports import export_rows
class FinalChecks(unittest.TestCase):
    def test_fixed_offset_winter_summer_and_rollovers(self):
        cases = [(datetime(2026,1,1,2,3,59,999999,tzinfo=timezone.utc),"2025-12-31 21:03"),
                 (datetime(2026,7,1,12,30,tzinfo=timezone.utc),"2026-07-01 07:30"),
                 (datetime(2024,3,1,1,tzinfo=timezone.utc),"2024-02-29 20:00")]
        source = [{"id":str(i),"starts_at":instant,"title":"Unused"} for i,(instant,_) in enumerate(cases)]
        before = copy.deepcopy(source)
        result = export_rows(source)
        self.assertEqual(result,[{"id":str(i),"starts_at":expected} for i,(_,expected) in enumerate(cases)])
        self.assertEqual(source,before)
        self.assertIsNot(result,source)
        for old,new in zip(source,result): self.assertIsNot(old,new)
    def test_empty(self):
        source = []
        result = export_rows(source)
        self.assertEqual(result,[])
        self.assertIsNot(result,source)
