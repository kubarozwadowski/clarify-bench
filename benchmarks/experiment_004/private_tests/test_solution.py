from datetime import datetime, timezone
import os
import time
import unittest
from unittest.mock import patch
from timestamps import encode_timestamp
class FinalChecks(unittest.TestCase):
    def check_cases(self):
        for value in ("1970-01-01T00:00:00Z","1970-01-01T00:00:01Z","2000-02-29T12:34:56Z","2025-12-31T23:59:59Z","2026-07-01T12:00:00Z","2100-12-31T23:59:59Z"):
            with self.subTest(value=value):
                instant = datetime.strptime(value,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                expected = int((instant-datetime(1970,1,1,tzinfo=timezone.utc)).total_seconds())*1000
                actual = encode_timestamp(value)
                self.assertIs(type(actual),int)
                self.assertEqual(actual,expected)
    def test_provider_units(self):
        self.check_cases()
    @unittest.skipUnless(hasattr(time,"tzset"),"Host cannot change timezone")
    def test_independent_of_host_timezone(self):
        try:
            with patch.dict(os.environ,{"TZ":"UTC+7"}):
                time.tzset()
                self.check_cases()
        finally:
            time.tzset()
